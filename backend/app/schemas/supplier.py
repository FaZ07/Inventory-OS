from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.supplier import SupplierStatus


class SupplierCreate(BaseModel):
    name: str
    code: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    lead_time_days: int = 7


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    lead_time_days: Optional[int] = None
    status: Optional[SupplierStatus] = None
    notes: Optional[str] = None
    on_time_delivery_rate: Optional[float] = None
    quality_score: Optional[float] = None
    price_competitiveness: Optional[float] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    code: str
    contact_email: str
    contact_phone: Optional[str]
    address: Optional[str]
    country: Optional[str]
    status: SupplierStatus
    on_time_delivery_rate: float
    quality_score: float
    price_competitiveness: float
    lead_time_days: int
    total_orders: int
    composite_score: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierRankResponse(BaseModel):
    supplier_id: int
    name: str
    composite_score: float
    rank: int
    breakdown: dict
