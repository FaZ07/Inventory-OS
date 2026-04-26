from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime, Enum as SAEnum, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base


class WarehouseStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_sqft: Mapped[float] = mapped_column(Float, nullable=False)
    max_weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    current_utilization_pct: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[WarehouseStatus] = mapped_column(SAEnum(WarehouseStatus), default=WarehouseStatus.ACTIVE)
    manager_name: Mapped[str] = mapped_column(String(255), nullable=True)
    manager_email: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    stock_entries = relationship("StockEntry", back_populates="warehouse", lazy="select")
    outbound_shipments = relationship("Shipment", foreign_keys="Shipment.origin_warehouse_id", back_populates="origin_warehouse", lazy="select")
    inbound_shipments = relationship("Shipment", foreign_keys="Shipment.dest_warehouse_id", back_populates="dest_warehouse", lazy="select")

    __table_args__ = (
        Index("ix_warehouse_geo", "latitude", "longitude"),
    )


class StockEntry(Base):
    """Junction table: how many units of a product are in a given warehouse."""
    __tablename__ = "stock_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=0)
    bin_location: Mapped[str] = mapped_column(String(50), nullable=True)
    last_counted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="stock_entries")
    product = relationship("Product", back_populates="stock_entries")

    __table_args__ = (
        Index("ix_stock_wh_prod", "warehouse_id", "product_id", unique=True),
    )
