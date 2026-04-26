from sqlalchemy import String, Float, Integer, Text, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    FAILED = "failed"
    RETURNED = "returned"


class ShipmentCarrier(str, Enum):
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"
    USPS = "usps"
    INTERNAL = "internal"
    OTHER = "other"


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracking_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    origin_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)
    dest_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[ShipmentStatus] = mapped_column(SAEnum(ShipmentStatus), default=ShipmentStatus.PENDING)
    carrier: Mapped[ShipmentCarrier] = mapped_column(SAEnum(ShipmentCarrier), default=ShipmentCarrier.OTHER)

    # Route data (populated by Dijkstra route optimizer)
    origin_address: Mapped[str] = mapped_column(Text, nullable=True)
    destination_address: Mapped[str] = mapped_column(Text, nullable=True)
    route_distance_km: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=True)

    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    volume_m3: Mapped[float] = mapped_column(Float, nullable=True)

    dispatched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    delay_reason: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    order = relationship("Order", back_populates="shipments")
    origin_warehouse = relationship("Warehouse", foreign_keys=[origin_warehouse_id], back_populates="outbound_shipments")
    dest_warehouse = relationship("Warehouse", foreign_keys=[dest_warehouse_id], back_populates="inbound_shipments")
    events = relationship("ShipmentEvent", back_populates="shipment", order_by="ShipmentEvent.occurred_at", lazy="selectin")

    __table_args__ = (
        Index("ix_shipment_status", "status"),
        Index("ix_shipment_carrier", "carrier"),
    )


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ShipmentStatus] = mapped_column(SAEnum(ShipmentStatus), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    shipment = relationship("Shipment", back_populates="events")
