import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import List, Optional

from app.models.order import Order, OrderItem, OrderStatus, OrderPriority
from app.models.product import Product
from app.models.warehouse import StockEntry
from app.schemas.order import OrderCreate, OrderUpdate
from app.core.redis import cache_delete_pattern


class OrderService:

    @staticmethod
    def _generate_order_number(order_type: str) -> str:
        prefix = {"purchase": "PO", "sales": "SO", "transfer": "TR", "return": "RT"}.get(order_type, "OR")
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    @staticmethod
    async def create(db: AsyncSession, data: OrderCreate, created_by: int) -> Order:
        order_number = OrderService._generate_order_number(data.order_type.value)

        order = Order(
            order_number=order_number,
            order_type=data.order_type,
            priority=data.priority,
            status=OrderStatus.DRAFT,
            supplier_id=data.supplier_id,
            warehouse_id=data.warehouse_id,
            expected_delivery=data.expected_delivery,
            notes=data.notes,
            created_by=created_by,
        )
        db.add(order)
        await db.flush()

        subtotal = 0.0
        for item_data in data.items:
            product = (await db.execute(
                select(Product).where(Product.id == item_data.product_id, Product.is_active == True)
            )).scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")

            total_price = item_data.quantity * item_data.unit_price
            subtotal += total_price
            item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=total_price,
            )
            db.add(item)

        order.subtotal = round(subtotal, 2)
        order.tax_amount = round(subtotal * 0.1, 2)
        order.total_amount = round(order.subtotal + order.tax_amount - order.discount_amount, 2)
        await db.flush()
        await db.refresh(order, ["items"])
        await cache_delete_pattern("orders:*")
        await cache_delete_pattern("analytics:*")
        return order

    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: int) -> Order:
        result = await db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        order_type: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> tuple[List[Order], int]:
        stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count(Order.id))

        if status:
            stmt = stmt.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)
        if order_type:
            stmt = stmt.where(Order.order_type == order_type)
            count_stmt = count_stmt.where(Order.order_type == order_type)
        if priority:
            stmt = stmt.where(Order.priority == priority)
            count_stmt = count_stmt.where(Order.priority == priority)

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Order.created_at.desc())
        items = list((await db.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def update(db: AsyncSession, order_id: int, data: OrderUpdate) -> Order:
        order = await OrderService.get_by_id(db, order_id)

        if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise HTTPException(status_code=400, detail="Cannot update a completed or cancelled order")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(order, field, value)

        if data.status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.now(timezone.utc)
            await OrderService._fulfill_stock(db, order)

        await db.flush()
        await cache_delete_pattern("orders:*")
        await cache_delete_pattern("analytics:*")
        return order

    @staticmethod
    async def _fulfill_stock(db: AsyncSession, order: Order):
        """Deduct stock from warehouse when sales order is delivered."""
        if not order.warehouse_id:
            return
        for item in order.items:
            entry = (await db.execute(
                select(StockEntry).where(
                    StockEntry.warehouse_id == order.warehouse_id,
                    StockEntry.product_id == item.product_id,
                )
            )).scalar_one_or_none()
            if entry:
                entry.quantity = max(0, entry.quantity - item.quantity)

    @staticmethod
    async def cancel(db: AsyncSession, order_id: int):
        order = await OrderService.get_by_id(db, order_id)
        if order.status == OrderStatus.DELIVERED:
            raise HTTPException(status_code=400, detail="Cannot cancel a delivered order")
        order.status = OrderStatus.CANCELLED
        await db.flush()
        await cache_delete_pattern("orders:*")
