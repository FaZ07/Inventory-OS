from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.shipment import ShipmentStatus, ShipmentCarrier


class ShipmentCreate(BaseModel):
    order_id: Optional[int] = None
    origin_warehouse_id: Optional[int] = None
    dest_warehouse_id: Optional[int] = None
    carrier: ShipmentCarrier = ShipmentCarrier.OTHER
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    estimated_arrival: Optional[datetime] = None


class ShipmentUpdate(BaseModel):
    status: Optional[ShipmentStatus] = None
    carrier: Optional[ShipmentCarrier] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    delay_reason: Optional[str] = None
    notes: Optional[str] = None


class ShipmentEventResponse(BaseModel):
    id: int
    status: ShipmentStatus
    location: Optional[str]
    description: Optional[str]
    occurred_at: datetime

    model_config = {"from_attributes": True}


class ShipmentResponse(BaseModel):
    id: int
    tracking_number: str
    order_id: Optional[int]
    origin_warehouse_id: Optional[int]
    dest_warehouse_id: Optional[int]
    status: ShipmentStatus
    carrier: ShipmentCarrier
    origin_address: Optional[str]
    destination_address: Optional[str]
    route_distance_km: Optional[float]
    estimated_cost: Optional[float]
    weight_kg: Optional[float]
    dispatched_at: Optional[datetime]
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    delay_reason: Optional[str]
    events: List[ShipmentEventResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
