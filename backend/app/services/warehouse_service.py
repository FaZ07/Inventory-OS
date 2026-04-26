from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
from typing import List

from app.models.warehouse import Warehouse, StockEntry, WarehouseStatus
from app.models.product import Product
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, StockUpdate
from app.algorithms.graph import WarehouseGraph
from app.core.redis import cache_get, cache_delete_pattern


class WarehouseService:

    @staticmethod
    async def create(db: AsyncSession, data: WarehouseCreate) -> Warehouse:
        existing = (await db.execute(select(Warehouse).where(Warehouse.code == data.code.upper()))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail=f"Warehouse code '{data.code}' already exists")

        wh = Warehouse(**data.model_dump())
        wh.code = wh.code.upper()
        db.add(wh)
        await db.flush()
        await cache_delete_pattern("warehouses:*")
        return wh

    @staticmethod
    async def get_by_id(db: AsyncSession, wh_id: int) -> Warehouse:
        result = await db.execute(select(Warehouse).where(Warehouse.id == wh_id, Warehouse.is_active == True))
        wh = result.scalar_one_or_none()
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        return wh

    @staticmethod
    async def list_warehouses(db: AsyncSession) -> List[Warehouse]:
        cached = await cache_get("warehouses:all")
        if cached:
            return cached
        result = await db.execute(select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.name))
        whs = list(result.scalars().all())
        return whs

    @staticmethod
    async def update(db: AsyncSession, wh_id: int, data: WarehouseUpdate) -> Warehouse:
        wh = await WarehouseService.get_by_id(db, wh_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(wh, field, value)
        await db.flush()
        await cache_delete_pattern("warehouses:*")
        return wh

    @staticmethod
    async def delete(db: AsyncSession, wh_id: int):
        wh = await WarehouseService.get_by_id(db, wh_id)
        wh.is_active = False
        wh.status = WarehouseStatus.CLOSED
        await db.flush()
        await cache_delete_pattern("warehouses:*")

    @staticmethod
    async def update_stock(
        db: AsyncSession, wh_id: int, product_id: int, data: StockUpdate
    ) -> StockEntry:
        await WarehouseService.get_by_id(db, wh_id)
        product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        entry = (await db.execute(
            select(StockEntry).where(
                and_(StockEntry.warehouse_id == wh_id, StockEntry.product_id == product_id)
            )
        )).scalar_one_or_none()

        if not entry:
            entry = StockEntry(warehouse_id=wh_id, product_id=product_id)
            db.add(entry)

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(entry, field, value)

        await db.flush()
        await WarehouseService._recalculate_utilization(db, wh_id)
        return entry

    @staticmethod
    async def get_stock(db: AsyncSession, wh_id: int) -> List[dict]:
        result = await db.execute(
            select(StockEntry, Product.sku, Product.name, Product.category)
            .join(Product, Product.id == StockEntry.product_id)
            .where(StockEntry.warehouse_id == wh_id)
        )
        return [
            {
                "product_id": r[0].product_id,
                "sku": r[1], "name": r[2], "category": r[3],
                "quantity": r[0].quantity,
                "reserved_quantity": r[0].reserved_quantity,
                "available": r[0].quantity - r[0].reserved_quantity,
                "reorder_point": r[0].reorder_point,
                "bin_location": r[0].bin_location,
                "needs_reorder": r[0].quantity <= r[0].reorder_point,
            }
            for r in result
        ]

    @staticmethod
    async def optimize_route(db: AsyncSession, origin_id: int, dest_id: int) -> dict:
        """Build warehouse graph and run Dijkstra for optimal shipping route."""
        result = await db.execute(
            select(Warehouse.id, Warehouse.latitude, Warehouse.longitude, Warehouse.name)
            .where(Warehouse.is_active == True)
        )
        warehouses = [{"id": r[0], "latitude": r[1], "longitude": r[2], "name": r[3]} for r in result]

        if not warehouses:
            raise HTTPException(status_code=400, detail="No active warehouses to build route")

        graph = WarehouseGraph()
        graph.build_from_warehouses(warehouses, full_mesh=True)

        route = graph.dijkstra(origin_id, dest_id)
        if not route:
            raise HTTPException(status_code=400, detail="No route found between warehouses")

        # Map warehouse IDs to names
        wh_names = {r["id"]: r["name"] for r in warehouses}
        route_dict = route.to_dict()
        route_dict["path_names"] = [wh_names.get(wid, str(wid)) for wid in route.path]

        bottlenecks = graph.find_bottlenecks()
        route_dict["network_bottlenecks"] = bottlenecks

        return route_dict

    @staticmethod
    async def _recalculate_utilization(db: AsyncSession, wh_id: int):
        wh = await WarehouseService.get_by_id(db, wh_id)
        result = await db.execute(
            select(func.sum(StockEntry.quantity * Product.weight_kg))
            .join(Product, Product.id == StockEntry.product_id)
            .where(StockEntry.warehouse_id == wh_id)
        )
        total_weight = float(result.scalar_one() or 0)
        if wh.max_weight_kg and wh.max_weight_kg > 0:
            wh.current_utilization_pct = min(100.0, total_weight / wh.max_weight_kg * 100)
        await db.flush()
