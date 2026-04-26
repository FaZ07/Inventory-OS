from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.models.product import Product
from app.models.warehouse import Warehouse, StockEntry
from app.models.order import Order, OrderItem, OrderStatus, OrderType
from app.models.supplier import Supplier
from app.models.shipment import Shipment, ShipmentStatus
from app.algorithms.forecasting import holt_winters_forecast, rank_suppliers
from app.algorithms.heap import RestockHeap
from app.core.redis import cache_get, cache_set


class AnalyticsService:

    @staticmethod
    async def dashboard_kpis(db: AsyncSession) -> Dict[str, Any]:
        cache_key = "analytics:dashboard_kpis"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total products
        total_products = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar_one()

        # Total warehouses
        total_warehouses = (await db.execute(select(func.count(Warehouse.id)).where(Warehouse.is_active == True))).scalar_one()

        # Total suppliers
        total_suppliers = (await db.execute(select(func.count(Supplier.id)).where(Supplier.is_active == True))).scalar_one()

        # Monthly revenue (delivered sales orders)
        revenue_result = await db.execute(
            select(func.sum(Order.total_amount)).where(
                and_(
                    Order.order_type == OrderType.SALES,
                    Order.status == OrderStatus.DELIVERED,
                    Order.created_at >= month_start,
                )
            )
        )
        monthly_revenue = float(revenue_result.scalar_one() or 0)

        # Pending orders count
        pending_orders = (await db.execute(
            select(func.count(Order.id)).where(Order.status.in_(["pending", "approved", "processing"]))
        )).scalar_one()

        # Active shipments
        active_shipments = (await db.execute(
            select(func.count(Shipment.id)).where(
                Shipment.status.in_(["picked_up", "in_transit", "out_for_delivery"])
            )
        )).scalar_one()

        # Low stock alerts
        low_stock = (await db.execute(
            select(func.count(StockEntry.id)).where(
                and_(
                    StockEntry.quantity > 0,
                    StockEntry.quantity <= StockEntry.reorder_point,
                )
            )
        )).scalar_one()

        # Avg warehouse utilization
        util_result = await db.execute(
            select(func.avg(Warehouse.current_utilization_pct)).where(Warehouse.is_active == True)
        )
        avg_utilization = round(float(util_result.scalar_one() or 0), 1)

        result = {
            "total_products": total_products,
            "total_warehouses": total_warehouses,
            "total_suppliers": total_suppliers,
            "monthly_revenue": round(monthly_revenue, 2),
            "pending_orders": pending_orders,
            "active_shipments": active_shipments,
            "low_stock_alerts": low_stock,
            "avg_warehouse_utilization_pct": avg_utilization,
            "generated_at": now.isoformat(),
        }
        await cache_set(cache_key, result, ttl=120)
        return result

    @staticmethod
    async def revenue_trend(db: AsyncSession, days: int = 30) -> List[Dict]:
        cache_key = f"analytics:revenue_trend:{days}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(text("""
            SELECT DATE(created_at) as day,
                   SUM(total_amount) as revenue,
                   COUNT(*) as order_count
            FROM orders
            WHERE order_type = 'sales'
              AND status = 'delivered'
              AND created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """).bindparams(days=days))

        rows = [{"date": str(r[0]), "revenue": float(r[1] or 0), "orders": int(r[2])} for r in result]
        await cache_set(cache_key, rows, ttl=300)
        return rows

    @staticmethod
    async def warehouse_utilization(db: AsyncSession) -> List[Dict]:
        result = await db.execute(
            select(
                Warehouse.id, Warehouse.name, Warehouse.city, Warehouse.country,
                Warehouse.capacity_sqft, Warehouse.current_utilization_pct,
                Warehouse.status
            ).where(Warehouse.is_active == True)
        )
        return [
            {
                "id": r[0], "name": r[1], "city": r[2], "country": r[3],
                "capacity_sqft": r[4], "utilization_pct": round(float(r[5]), 1),
                "status": r[6],
            }
            for r in result
        ]

    @staticmethod
    async def top_products_by_revenue(db: AsyncSession, limit: int = 10) -> List[Dict]:
        cache_key = f"analytics:top_products:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(
            select(
                Product.id, Product.sku, Product.name, Product.category,
                func.sum(OrderItem.total_price).label("total_revenue"),
                func.sum(OrderItem.quantity).label("total_units"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == OrderStatus.DELIVERED)
            .group_by(Product.id, Product.sku, Product.name, Product.category)
            .order_by(func.sum(OrderItem.total_price).desc())
            .limit(limit)
        )
        rows = [
            {
                "product_id": r[0], "sku": r[1], "name": r[2], "category": r[3],
                "total_revenue": round(float(r[4] or 0), 2),
                "total_units_sold": int(r[5] or 0),
            }
            for r in result
        ]
        await cache_set(cache_key, rows, ttl=300)
        return rows

    @staticmethod
    async def get_restock_queue(db: AsyncSession) -> List[dict]:
        """Use RestockHeap to return prioritised restock recommendations."""
        result = await db.execute(
            select(
                StockEntry.product_id, StockEntry.warehouse_id,
                StockEntry.quantity, StockEntry.reorder_point,
                Product.sku, Product.name, Product.avg_daily_demand,
            )
            .join(Product, Product.id == StockEntry.product_id)
            .where(StockEntry.quantity <= StockEntry.reorder_point)
            .where(Product.is_active == True)
        )
        heap = RestockHeap()
        for row in result:
            heap.push_stock_entry(
                product_id=row[0], sku=row[4], name=row[5],
                warehouse_id=row[1], current_stock=row[2],
                reorder_point=row[3], avg_daily_demand=float(row[6]),
            )
        items = heap.top_k_critical(50)
        return [
            {
                "product_id": i.product_id, "sku": i.sku, "name": i.name,
                "warehouse_id": i.warehouse_id, "current_stock": i.current_stock,
                "reorder_point": i.reorder_point, "days_until_stockout": i.days_until_stockout,
                "urgency_score": i.urgency_score,
            }
            for i in items
        ]

    @staticmethod
    async def supplier_rankings(db: AsyncSession) -> List[dict]:
        result = await db.execute(
            select(
                Supplier.id, Supplier.name,
                Supplier.on_time_delivery_rate, Supplier.quality_score,
                Supplier.price_competitiveness, Supplier.lead_time_days,
            ).where(Supplier.is_active == True)
        )
        suppliers = [
            {
                "id": r[0], "name": r[1],
                "on_time_delivery_rate": float(r[2]),
                "quality_score": float(r[3]),
                "price_competitiveness": float(r[4]),
                "lead_time_days": r[5],
            }
            for r in result
        ]
        ranked = rank_suppliers(suppliers)
        return [
            {
                "supplier_id": s.supplier_id, "name": s.name,
                "composite_score": s.composite_score, "rank": s.rank,
                "breakdown": s.breakdown,
            }
            for s in ranked
        ]

    @staticmethod
    async def demand_forecast(db: AsyncSession, product_id: int, periods: int = 30) -> dict:
        cache_key = f"analytics:forecast:{product_id}:{periods}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(text("""
            SELECT DATE(o.created_at) as day, SUM(oi.quantity)::float as qty
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE oi.product_id = :pid
              AND o.status = 'delivered'
              AND o.created_at >= NOW() - INTERVAL '180 days'
            GROUP BY DATE(o.created_at)
            ORDER BY day ASC
        """).bindparams(pid=product_id))

        history = [float(r[1]) for r in result]
        if len(history) < 14:
            return {"error": "Insufficient history for forecasting", "min_required": 14}

        forecast = holt_winters_forecast(history, periods_ahead=periods)
        out = {
            "product_id": product_id,
            "periods_ahead": periods,
            "forecast": forecast.forecast,
            "trend": forecast.trend,
            "rmse": forecast.rmse,
            "mape": forecast.mape,
            "confidence_lower": forecast.confidence_lower,
            "confidence_upper": forecast.confidence_upper,
        }
        await cache_set(cache_key, out, ttl=3600)
        return out

    @staticmethod
    async def supply_chain_health(db: AsyncSession) -> dict:
        on_time = (await db.execute(
            select(func.count(Shipment.id)).where(
                and_(
                    Shipment.status == ShipmentStatus.DELIVERED,
                    Shipment.actual_arrival <= Shipment.estimated_arrival,
                )
            )
        )).scalar_one()

        total_delivered = (await db.execute(
            select(func.count(Shipment.id)).where(Shipment.status == ShipmentStatus.DELIVERED)
        )).scalar_one()

        delayed = (await db.execute(
            select(func.count(Shipment.id)).where(Shipment.status == ShipmentStatus.DELAYED)
        )).scalar_one()

        on_time_rate = round(on_time / max(total_delivered, 1) * 100, 1)

        return {
            "on_time_delivery_rate_pct": on_time_rate,
            "total_delivered": total_delivered,
            "currently_delayed": delayed,
            "health_score": round(on_time_rate * 0.6 + max(0, 100 - delayed * 5) * 0.4, 1),
        }
