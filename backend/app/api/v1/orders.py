from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.order_service import OrderService
from app.algorithms.heap import OrderHeap
from datetime import datetime, timezone

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    return await OrderService.create(db, data, current_user.id)


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    items, total = await OrderService.list_orders(db, page, page_size, status, order_type, priority)
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/priority-queue")
async def get_priority_queue(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
    top_k: int = Query(20, ge=1, le=100),
):
    """
    Binary heap-based order urgency ranking.
    Returns top-K most urgent orders (priority × age × value).
    """
    from sqlalchemy import select
    from app.models.order import Order, OrderStatus
    result = await db.execute(
        select(Order).where(Order.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]))
    )
    orders = result.scalars().all()

    heap = OrderHeap()
    now = datetime.now(timezone.utc)
    for o in orders:
        due = o.expected_delivery
        days_until = (due.replace(tzinfo=timezone.utc) - now).days if due else 0
        heap.push_order(
            order_id=o.id,
            order_number=o.order_number,
            priority=o.priority.value,
            days_until_due=float(days_until),
            total_value=o.total_amount,
            status=o.status.value,
        )

    ranked = heap.top_k(top_k)
    return [
        {
            "order_id": r.order_id,
            "order_number": r.order_number,
            "priority": r.priority_label,
            "urgency_score": r.urgency_score,
            "days_overdue": r.days_overdue,
            "total_value": r.total_value,
            "status": r.status,
        }
        for r in ranked
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await OrderService.get_by_id(db, order_id)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int, data: OrderUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_manager),
):
    return await OrderService.update(db, order_id, data)


@router.post("/{order_id}/cancel", response_model=MessageResponse)
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_manager)):
    await OrderService.cancel(db, order_id)
    return MessageResponse(message="Order cancelled")
