from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"
    PROBATION = "probation"


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[SupplierStatus] = mapped_column(SAEnum(SupplierStatus), default=SupplierStatus.ACTIVE)

    # Performance metrics (updated by DSA scoring algorithm)
    on_time_delivery_rate: Mapped[float] = mapped_column(Float, default=1.0)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0)
    price_competitiveness: Mapped[float] = mapped_column(Float, default=1.0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_defects: Mapped[int] = mapped_column(Integer, default=0)
    composite_score: Mapped[float] = mapped_column(Float, default=1.0)

    contract_start: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_end: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    products = relationship("Product", back_populates="supplier", lazy="select")
    purchase_orders = relationship("Order", back_populates="supplier", lazy="select")

    __table_args__ = (
        Index("ix_supplier_score", "composite_score"),
    )
