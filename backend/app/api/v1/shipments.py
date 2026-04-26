import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager
from app.models.shipment import Shipment, ShipmentEvent, ShipmentStatus
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.algorithms.heap import ShipmentRiskHeap
from app.core.redis import cache_delete_pattern
import time

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.post("", response_model=ShipmentResponse, status_code=201)
async def create_shipment(
    data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager),
):
    tracking = f"IOS-{uuid.uuid4().hex[:10].upper()}"
    shipment = Shipment(**data.model_dump(), tracking_number=tracking)
    db.add(shipment)
    await db.flush()

    # Record initial event
    event = ShipmentEvent(shipment_id=shipment.id, status=ShipmentStatus.PENDING, description="Shipment created")
    db.add(event)
    await db.flush()
    await db.refresh(shipment, ["events"])
    await cache_delete_pattern("shipments:*")
    return shipment


@router.get("", response_model=PaginatedResponse[ShipmentResponse])
async def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    stmt = select(Shipment).options(selectinload(Shipment.events))
    count_stmt = select(func.count(Shipment.id))

    if status:
        stmt = stmt.where(Shipment.status == status)
        count_stmt = count_stmt.where(Shipment.status == status)
    if carrier:
        stmt = stmt.where(Shipment.carrier == carrier)
        count_stmt = count_stmt.where(Shipment.carrier == carrier)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Shipment.created_at.desc())
    items = list((await db.execute(stmt)).scalars().all())
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/delay-risk")
async def get_delay_risk_queue(
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """ShipmentRiskHeap — ranks in-transit shipments by delay risk score."""
    result = await db.execute(
        select(Shipment).where(Shipment.status.in_(["in_transit", "picked_up", "out_for_delivery"]))
    )
    shipments = result.scalars().all()
    heap = ShipmentRiskHeap()
    for s in shipments:
        eta_ts = s.estimated_arrival.timestamp() if s.estimated_arrival else time.time()
        heap.push_shipment(s.id, s.tracking_number, s.carrier.value, eta_ts, s.status.value)
    return [
        {"shipment_id": r.shipment_id, "tracking_number": r.tracking_number,
         "carrier": r.carrier, "days_delayed": r.days_delayed, "risk_score": r.risk_score}
        for r in heap.top_k_delayed(top_k)
    ]


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    from fastapi import HTTPException
    result = await db.execute(
        select(Shipment).options(selectinload(Shipment.events)).where(Shipment.id == shipment_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: int, data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_manager),
):
    from fastapi import HTTPException
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Shipment).options(selectinload(Shipment.events)).where(Shipment.id == shipment_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    old_status = shipment.status
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(shipment, field, value)

    if data.status and data.status != old_status:
        event = ShipmentEvent(shipment_id=shipment.id, status=data.status)
        db.add(event)

    await db.flush()
    await cache_delete_pattern("shipments:*")
    return shipment
