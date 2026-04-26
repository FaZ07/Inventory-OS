from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_manager
from app.services.analytics_service import AnalyticsService
from app.algorithms.forecasting import dp_replenishment

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_kpis(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Real-time KPIs: revenue, orders, shipments, alerts, utilization."""
    return await AnalyticsService.dashboard_kpis(db)


@router.get("/revenue-trend")
async def revenue_trend(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await AnalyticsService.revenue_trend(db, days)


@router.get("/warehouse-utilization")
async def warehouse_utilization(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await AnalyticsService.warehouse_utilization(db)


@router.get("/top-products")
async def top_products(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await AnalyticsService.top_products_by_revenue(db, limit)


@router.get("/restock-queue")
async def restock_queue(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """
    RestockHeap — priority-queued list of SKUs by stockout urgency.
    Use this to drive automated reorder workflows.
    """
    return await AnalyticsService.get_restock_queue(db)


@router.get("/supplier-rankings")
async def supplier_rankings(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await AnalyticsService.supplier_rankings(db)


@router.get("/forecast/{product_id}")
async def demand_forecast(
    product_id: int,
    periods: int = Query(30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Holt-Winters triple exponential smoothing forecast.
    Returns forecast, confidence intervals, RMSE, and MAPE.
    """
    return await AnalyticsService.demand_forecast(db, product_id, periods)


@router.post("/replenishment-plan")
async def replenishment_plan(
    demand_forecast: list[float],
    holding_cost_per_unit_period: float = Query(0.5, gt=0),
    ordering_cost: float = Query(100.0, gt=0),
    initial_stock: int = Query(0, ge=0),
    _=Depends(require_manager),
):
    """
    Wagner-Whitin DP lot-sizing algorithm.
    Returns globally optimal order quantities to minimise holding + ordering costs.
    """
    plan = dp_replenishment(
        demand_forecast=demand_forecast,
        holding_cost_per_unit_period=holding_cost_per_unit_period,
        ordering_cost=ordering_cost,
        initial_stock=initial_stock,
    )
    return {
        "order_quantities": plan.order_quantities,
        "total_cost": plan.total_cost,
        "total_ordered": plan.total_ordered,
        "avg_inventory": plan.avg_inventory,
        "periods": plan.periods,
    }


@router.get("/supply-chain-health")
async def supply_chain_health(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await AnalyticsService.supply_chain_health(db)
