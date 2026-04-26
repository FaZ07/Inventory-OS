from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.warehouse import WarehouseStatus


class WarehouseCreate(BaseModel):
    name: str
    code: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    capacity_sqft: float
    max_weight_kg: Optional[float] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    capacity_sqft: Optional[float] = None
    max_weight_kg: Optional[float] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    status: Optional[WarehouseStatus] = None
    current_utilization_pct: Optional[float] = None


class WarehouseResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    capacity_sqft: float
    max_weight_kg: Optional[float]
    current_utilization_pct: float
    status: WarehouseStatus
    manager_name: Optional[str]
    manager_email: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StockUpdate(BaseModel):
    quantity: int
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    bin_location: Optional[str] = None


class RouteRequest(BaseModel):
    origin_warehouse_id: int
    destination_warehouse_id: int
