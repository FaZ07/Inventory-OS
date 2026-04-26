import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional, List

from app.models.product import Product, ProductStatus
from app.models.warehouse import StockEntry
from app.schemas.product import ProductCreate, ProductUpdate
from app.algorithms.trie import get_trie, rebuild_trie
from app.core.redis import cache_get, cache_set, cache_delete, cache_delete_pattern
from app.core.config import settings


class ProductService:

    @staticmethod
    async def create(db: AsyncSession, data: ProductCreate) -> Product:
        existing = await db.execute(select(Product).where(Product.sku == data.sku))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"SKU '{data.sku}' already exists")

        product = Product(**data.model_dump())
        db.add(product)
        await db.flush()
        await db.refresh(product)
        await cache_delete_pattern("products:*")
        trie = get_trie()
        trie.insert(product.sku, product.name, product.id, product.turnover_rate)
        return product

    @staticmethod
    async def get_by_id(db: AsyncSession, product_id: int) -> Product:
        cache_key = f"products:{product_id}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(select(Product).where(Product.id == product_id, Product.is_active == True))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @staticmethod
    async def list_products(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        supplier_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Product], int]:
        cache_key = f"products:list:{page}:{page_size}:{category}:{status}:{supplier_id}:{search}"
        cached = await cache_get(cache_key)
        if cached:
            return cached["items"], cached["total"]

        stmt = select(Product).where(Product.is_active == True)
        count_stmt = select(func.count(Product.id)).where(Product.is_active == True)

        if category:
            stmt = stmt.where(Product.category == category)
            count_stmt = count_stmt.where(Product.category == category)
        if status:
            stmt = stmt.where(Product.status == status)
            count_stmt = count_stmt.where(Product.status == status)
        if supplier_id:
            stmt = stmt.where(Product.supplier_id == supplier_id)
            count_stmt = count_stmt.where(Product.supplier_id == supplier_id)

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Product.id.desc())
        items = list((await db.execute(stmt)).scalars().all())

        await cache_set(cache_key, {"items": [p.id for p in items], "total": total}, ttl=60)
        return items, total

    @staticmethod
    async def update(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product:
        product = await ProductService.get_by_id(db, product_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        await db.flush()
        await cache_delete_pattern("products:*")
        return product

    @staticmethod
    async def delete(db: AsyncSession, product_id: int):
        product = await ProductService.get_by_id(db, product_id)
        product.is_active = False
        product.status = ProductStatus.DISCONTINUED
        await db.flush()
        await cache_delete_pattern("products:*")

    @staticmethod
    async def trie_search(query: str, fuzzy: bool = False, top_k: int = 10) -> List[dict]:
        trie = get_trie()
        if fuzzy:
            results = trie.fuzzy_search(query, max_distance=1, top_k=top_k)
        else:
            results = trie.autocomplete(query, top_k=top_k)
        return results

    @staticmethod
    async def rebuild_search_index(db: AsyncSession):
        result = await db.execute(
            select(Product.id, Product.sku, Product.name, Product.turnover_rate)
            .where(Product.is_active == True)
        )
        products = [{"id": r[0], "sku": r[1], "name": r[2], "turnover_rate": r[3]} for r in result]
        rebuild_trie(products)
        return len(products)

    @staticmethod
    async def update_stock_aggregate(db: AsyncSession, product_id: int):
        """Recalculate total_quantity from stock_entries and update product row."""
        result = await db.execute(
            select(func.sum(StockEntry.quantity)).where(StockEntry.product_id == product_id)
        )
        total = result.scalar_one() or 0
        await db.execute(
            update(Product).where(Product.id == product_id).values(total_quantity=total)
        )
