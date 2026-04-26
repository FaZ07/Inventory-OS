from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from app.models.order import OrderType, OrderStatus, OrderPriority


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class OrderCreate(BaseModel):
    order_type: OrderType
    priority: OrderPriority = OrderPriority.MEDIUM
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Order must have at least one item")
        return v


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    quantity_received: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    order_number: str
    order_type: OrderType
    status: OrderStatus
    priority: OrderPriority
    supplier_id: Optional[int]
    warehouse_id: Optional[int]
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    currency: str
    expected_delivery: Optional[datetime]
    delivered_at: Optional[datetime]
    notes: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
