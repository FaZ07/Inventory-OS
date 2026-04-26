from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager, require_admin
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierRankResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.analytics_service import AnalyticsService
from app.core.redis import cache_delete_pattern

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(data: SupplierCreate, db: AsyncSession = Depends(get_db), _=Depends(require_manager)):
    from fastapi import HTTPException
    existing = (await db.execute(select(Supplier).where(Supplier.code == data.code.upper()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Supplier code '{data.code}' already exists")
    supplier = Supplier(**data.model_dump())
    supplier.code = supplier.code.upper()
    db.add(supplier)
    await db.flush()
    await db.refresh(supplier)
    await cache_delete_pattern("suppliers:*")
    return supplier


@router.get("", response_model=PaginatedResponse[SupplierResponse])
async def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Supplier).where(Supplier.is_active == True)
    count_stmt = select(func.count(Supplier.id)).where(Supplier.is_active == True)
    if status:
        stmt = stmt.where(Supplier.status == status)
        count_stmt = count_stmt.where(Supplier.status == status)
    if country:
        stmt = stmt.where(Supplier.country == country)
        count_stmt = count_stmt.where(Supplier.country == country)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Supplier.composite_score.desc())
    items = list((await db.execute(stmt)).scalars().all())
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/rankings", response_model=list[SupplierRankResponse])
async def supplier_rankings(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """
    Multi-factor weighted supplier ranking using merge-sort.
    Factors: on-time delivery, quality, pricing, lead time.
    """
    return await AnalyticsService.supplier_rankings(db)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    from fastapi import HTTPException
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_active == True))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int, data: SupplierUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_manager),
):
    from fastapi import HTTPException
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(supplier, field, value)
    await db.flush()
    await cache_delete_pattern("suppliers:*")
    return supplier


@router.delete("/{supplier_id}", response_model=MessageResponse)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    from fastapi import HTTPException
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = False
    await db.flush()
    await cache_delete_pattern("suppliers:*")
    return MessageResponse(message="Supplier deactivated")
