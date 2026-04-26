from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from app.models.product import ProductStatus, ProductCategory


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: ProductCategory
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    unit_cost: float
    unit_price: float
    currency: str = "USD"
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    min_stock_level: int = 0
    max_stock_level: int = 0
    supplier_id: Optional[int] = None

    @field_validator("unit_price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    @field_validator("sku")
    @classmethod
    def sku_upper(cls, v: str) -> str:
        return v.upper().strip()


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    supplier_id: Optional[int] = None
    status: Optional[ProductStatus] = None


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: ProductCategory
    sub_category: Optional[str]
    brand: Optional[str]
    barcode: Optional[str]
    unit_cost: float
    unit_price: float
    currency: str
    weight_kg: Optional[float]
    volume_m3: Optional[float]
    total_quantity: int
    min_stock_level: int
    max_stock_level: int
    avg_daily_demand: float
    turnover_rate: float
    supplier_id: Optional[int]
    status: ProductStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ProductSearchResult(BaseModel):
    product_id: int
    sku: str
    name: str
    score: float
    edit_distance: Optional[int] = None
