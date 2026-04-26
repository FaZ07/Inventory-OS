from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base


class ProductStatus(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    PENDING = "pending"
    OUT_OF_STOCK = "out_of_stock"


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    MACHINERY = "machinery"
    CHEMICALS = "chemicals"
    FURNITURE = "furniture"
    MEDICAL = "medical"
    OTHER = "other"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[ProductCategory] = mapped_column(SAEnum(ProductCategory), nullable=False)
    sub_category: Mapped[str] = mapped_column(String(100), nullable=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=True)
    barcode: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)

    # Pricing
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Physical
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    volume_m3: Mapped[float] = mapped_column(Float, nullable=True)

    # Stock totals (aggregated across all warehouses for fast reads)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    max_stock_level: Mapped[int] = mapped_column(Integer, default=0)

    # Analytics fields updated by forecasting engine
    avg_daily_demand: Mapped[float] = mapped_column(Float, default=0.0)
    demand_variance: Mapped[float] = mapped_column(Float, default=0.0)
    turnover_rate: Mapped[float] = mapped_column(Float, default=0.0)

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(SAEnum(ProductStatus), default=ProductStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    supplier = relationship("Supplier", back_populates="products")
    stock_entries = relationship("StockEntry", back_populates="product", lazy="select")
    order_items = relationship("OrderItem", back_populates="product", lazy="select")

    __table_args__ = (
        Index("ix_product_category", "category"),
        Index("ix_product_status", "status"),
        Index("ix_product_turnover", "turnover_rate"),
    )
