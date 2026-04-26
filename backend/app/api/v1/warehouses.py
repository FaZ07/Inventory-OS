from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager, require_admin
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse, StockUpdate, RouteRequest
from app.schemas.common import MessageResponse
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.post("", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(data: WarehouseCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    return await WarehouseService.create(db, data)


@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await WarehouseService.list_warehouses(db)


@router.get("/{wh_id}", response_model=WarehouseResponse)
async def get_warehouse(wh_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await WarehouseService.get_by_id(db, wh_id)


@router.patch("/{wh_id}", response_model=WarehouseResponse)
async def update_warehouse(wh_id: int, data: WarehouseUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_manager)):
    return await WarehouseService.update(db, wh_id, data)


@router.delete("/{wh_id}", response_model=MessageResponse)
async def delete_warehouse(wh_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    await WarehouseService.delete(db, wh_id)
    return MessageResponse(message="Warehouse deactivated")


@router.get("/{wh_id}/stock")
async def get_warehouse_stock(wh_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await WarehouseService.get_stock(db, wh_id)


@router.put("/{wh_id}/stock/{product_id}")
async def update_stock(
    wh_id: int, product_id: int, data: StockUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(require_manager),
):
    return await WarehouseService.update_stock(db, wh_id, product_id, data)


@router.post("/route/optimize")
async def optimize_route(
    data: RouteRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Dijkstra's algorithm — returns optimal path, cost, and distance
    between two warehouses through the shipping network.
    Also identifies network bottleneck nodes.
    """
    return await WarehouseService.optimize_route(db, data.origin_warehouse_id, data.destination_warehouse_id)
