"""
Demand forecasting and inventory optimisation via Dynamic Programming.

Algorithms:
  1. Triple Exponential Smoothing (Holt-Winters) — trend + seasonality
  2. DP Inventory Replenishment  — minimise holding + ordering costs
  3. Economic Order Quantity (EOQ) — classic optimal batch size
  4. Safety Stock Calculator     — service-level-driven buffer
  5. Supplier Score Ranker       — multi-factor weighted scoring
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict


# ── 1. Holt-Winters Triple Exponential Smoothing ──────────────────────────────

@dataclass
class ForecastResult:
    forecast: List[float]          # predicted demand per period
    trend: float                   # current trend component
    seasonality: List[float]       # seasonal factors
    rmse: float                    # root mean squared error on training data
    mape: float                    # mean absolute percentage error (%)
    confidence_lower: List[float]  # 95% lower bound
    confidence_upper: List[float]  # 95% upper bound


def holt_winters_forecast(
    history: List[float],
    periods_ahead: int = 12,
    season_length: int = 7,
    alpha: float = 0.3,
    beta: float = 0.1,
    gamma: float = 0.2,
) -> ForecastResult:
    """
    Triple exponential smoothing (additive model).

    α = level smoothing        [0, 1]
    β = trend smoothing        [0, 1]
    γ = seasonal smoothing     [0, 1]
    """
    n = len(history)
    if n < 2 * season_length:
        return _fallback_forecast(history, periods_ahead)

    # Initialise level, trend, seasonal components
    L = sum(history[:season_length]) / season_length
    T = (sum(history[season_length:2*season_length]) - sum(history[:season_length])) / season_length**2
    S = [history[i] / (L + 1e-9) for i in range(season_length)]

    fitted: List[float] = []
    Ls, Ts, Ss = L, T, S[:]

    for t, y in enumerate(history):
        s_idx = t % season_length
        L_prev, T_prev = Ls, Ts
        Ls = alpha * (y - Ss[s_idx]) + (1 - alpha) * (L_prev + T_prev)
        Ts = beta * (Ls - L_prev) + (1 - beta) * T_prev
        Ss[s_idx] = gamma * (y - Ls) + (1 - gamma) * Ss[s_idx]
        fitted.append(Ls + Ts + Ss[s_idx])

    # Compute error metrics
    errors = [abs(h - f) for h, f in zip(history, fitted)]
    rmse = math.sqrt(sum(e**2 for e in errors) / n)
    mape = sum(abs(e / (abs(h) + 1e-9)) for e, h in zip(errors, history)) / n * 100

    # Generate future forecasts
    forecast, lower, upper = [], [], []
    std = math.sqrt(sum(e**2 for e in errors[-season_length:]) / season_length + 1e-9)
    for m in range(1, periods_ahead + 1):
        val = Ls + m * Ts + Ss[(n - 1 + m) % season_length]
        val = max(0.0, val)
        forecast.append(round(val, 2))
        lower.append(round(max(0.0, val - 1.96 * std * math.sqrt(m)), 2))
        upper.append(round(val + 1.96 * std * math.sqrt(m), 2))

    return ForecastResult(
        forecast=forecast,
        trend=round(Ts, 4),
        seasonality=[round(s, 4) for s in Ss],
        rmse=round(rmse, 4),
        mape=round(mape, 2),
        confidence_lower=lower,
        confidence_upper=upper,
    )


def _fallback_forecast(history: List[float], periods_ahead: int) -> ForecastResult:
    avg = sum(history) / len(history) if history else 0.0
    return ForecastResult(
        forecast=[round(avg, 2)] * periods_ahead,
        trend=0.0, seasonality=[1.0],
        rmse=0.0, mape=0.0,
        confidence_lower=[max(0, avg * 0.8)] * periods_ahead,
        confidence_upper=[avg * 1.2] * periods_ahead,
    )


# ── 2. DP Inventory Replenishment Optimiser ───────────────────────────────────

@dataclass
class ReplenishmentPlan:
    order_quantities: List[int]     # how much to order each period
    total_cost: float               # total holding + ordering cost
    total_ordered: int
    avg_inventory: float
    periods: int


def dp_replenishment(
    demand_forecast: List[float],
    holding_cost_per_unit_period: float,
    ordering_cost: float,
    initial_stock: int = 0,
    min_order: int = 0,
    max_order: int = 10_000,
) -> ReplenishmentPlan:
    """
    DP lot-sizing: Wagner-Whitin algorithm.
    Finds the globally optimal ordering schedule over T periods to minimise:
      total_cost = Σ (ordering_cost × 1[order > 0]) + Σ (holding_cost × inventory_t)

    State: dp[t] = min cost to satisfy demand through period t
    Transition: dp[t] = min over j≤t of { dp[j-1] + setup + Σ holding[j..t] }

    Time: O(T²)   Space: O(T)
    """
    T = len(demand_forecast)
    if T == 0:
        return ReplenishmentPlan([], 0.0, 0, 0.0, 0)

    demand = [max(0.0, d) for d in demand_forecast]

    # Precompute cumulative demand for holding cost sums
    cum_demand = [0.0] * (T + 1)
    for t in range(T):
        cum_demand[t + 1] = cum_demand[t] + demand[t]

    INF = float("inf")
    dp = [INF] * (T + 1)
    dp[0] = 0.0
    last_order = [-1] * (T + 1)

    for t in range(1, T + 1):
        for j in range(1, t + 1):
            # Order at start of period j enough to cover j..t
            order_qty = cum_demand[t] - cum_demand[j - 1]
            if order_qty > max_order:
                continue
            # Holding cost: inventory carried in each period
            holding = sum(
                (cum_demand[t] - cum_demand[p]) * holding_cost_per_unit_period
                for p in range(j - 1, t)
            )
            cost = dp[j - 1] + ordering_cost + holding
            if cost < dp[t]:
                dp[t] = cost
                last_order[t] = j

    # Reconstruct order schedule
    orders = [0] * T
    t = T
    while t > 0 and last_order[t] != -1:
        j = last_order[t]
        orders[j - 1] = int(math.ceil(cum_demand[t] - cum_demand[j - 1]))
        t = j - 1

    # Apply initial stock
    if initial_stock > 0:
        remaining = initial_stock
        for i in range(T):
            reduction = min(orders[i], remaining)
            orders[i] = max(0, orders[i] - reduction)
            remaining -= reduction
            if remaining <= 0:
                break

    avg_inv = sum(
        max(0, initial_stock + sum(orders[:i]) - cum_demand[i])
        for i in range(T)
    ) / T

    return ReplenishmentPlan(
        order_quantities=orders,
        total_cost=round(dp[T], 2),
        total_ordered=sum(orders),
        avg_inventory=round(avg_inv, 2),
        periods=T,
    )


# ── 3. Economic Order Quantity ────────────────────────────────────────────────

@dataclass
class EOQResult:
    eoq: float
    annual_ordering_cost: float
    annual_holding_cost: float
    total_annual_cost: float
    orders_per_year: float
    cycle_days: float


def economic_order_quantity(
    annual_demand: float,
    ordering_cost: float,
    holding_cost_pct: float,
    unit_cost: float,
) -> EOQResult:
    """
    Wilson's EOQ formula:  Q* = sqrt(2DS / H)
    D = annual demand, S = ordering cost, H = holding cost per unit per year
    """
    H = holding_cost_pct * unit_cost
    eoq = math.sqrt(2 * annual_demand * ordering_cost / (H + 1e-9))
    orders_per_year = annual_demand / (eoq + 1e-9)
    return EOQResult(
        eoq=round(eoq, 1),
        annual_ordering_cost=round(orders_per_year * ordering_cost, 2),
        annual_holding_cost=round((eoq / 2) * H, 2),
        total_annual_cost=round(orders_per_year * ordering_cost + (eoq / 2) * H, 2),
        orders_per_year=round(orders_per_year, 2),
        cycle_days=round(365 / (orders_per_year + 1e-9), 1),
    )


# ── 4. Safety Stock ───────────────────────────────────────────────────────────

def safety_stock(
    avg_demand_per_day: float,
    demand_std: float,
    avg_lead_days: float,
    lead_std: float,
    service_level_pct: float = 0.95,
) -> int:
    """
    SS = Z × sqrt(L × σ_d² + d² × σ_L²)

    Z-scores: 90% → 1.28, 95% → 1.645, 99% → 2.33
    """
    z_map = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
    Z = z_map.get(service_level_pct, 1.645)
    ss = Z * math.sqrt(
        avg_lead_days * demand_std ** 2
        + avg_demand_per_day ** 2 * lead_std ** 2
    )
    return max(0, int(math.ceil(ss)))


# ── 5. Supplier Scoring (Multi-factor weighted ranking) ───────────────────────

@dataclass
class SupplierScore:
    supplier_id: int
    name: str
    composite_score: float
    rank: int
    breakdown: Dict[str, float]


def rank_suppliers(suppliers: List[dict]) -> List[SupplierScore]:
    """
    Composite scoring with configurable weights.
    Uses merge-sort internally for O(n log n) ranking.

    Factors:
      - On-time delivery rate   (weight 0.35)
      - Quality score           (weight 0.30)
      - Price competitiveness   (weight 0.20)
      - Lead time (inverted)    (weight 0.15)
    """
    WEIGHTS = {
        "on_time_delivery_rate": 0.35,
        "quality_score": 0.30,
        "price_competitiveness": 0.20,
        "lead_time_score": 0.15,
    }

    def normalise(values: List[float]) -> List[float]:
        mn, mx = min(values, default=0), max(values, default=1)
        rng = mx - mn or 1e-9
        return [(v - mn) / rng for v in values]

    if not suppliers:
        return []

    otd = normalise([s.get("on_time_delivery_rate", 1.0) for s in suppliers])
    qs = normalise([s.get("quality_score", 1.0) for s in suppliers])
    pc = normalise([s.get("price_competitiveness", 1.0) for s in suppliers])
    max_lead = max(s.get("lead_time_days", 7) for s in suppliers) or 1
    lt = [(max_lead - s.get("lead_time_days", 7)) / max_lead for s in suppliers]

    scored = []
    for i, s in enumerate(suppliers):
        score = (
            WEIGHTS["on_time_delivery_rate"] * otd[i]
            + WEIGHTS["quality_score"] * qs[i]
            + WEIGHTS["price_competitiveness"] * pc[i]
            + WEIGHTS["lead_time_score"] * lt[i]
        )
        scored.append(SupplierScore(
            supplier_id=s.get("id", i),
            name=s.get("name", ""),
            composite_score=round(score, 4),
            rank=0,
            breakdown={
                "on_time_delivery": round(otd[i], 4),
                "quality": round(qs[i], 4),
                "price": round(pc[i], 4),
                "lead_time": round(lt[i], 4),
            },
        ))

    # Merge sort descending by composite_score
    scored = _merge_sort(scored, key=lambda x: x.composite_score, reverse=True)
    for rank, ss in enumerate(scored, 1):
        ss.rank = rank

    return scored


def _merge_sort(arr: list, key=lambda x: x, reverse: bool = False) -> list:
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = _merge_sort(arr[:mid], key, reverse)
    right = _merge_sort(arr[mid:], key, reverse)
    return _merge(left, right, key, reverse)


def _merge(left: list, right: list, key, reverse: bool) -> list:
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        lv, rv = key(left[i]), key(right[j])
        if (lv >= rv) if reverse else (lv <= rv):
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]
