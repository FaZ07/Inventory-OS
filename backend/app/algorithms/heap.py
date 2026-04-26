"""
Binary Min-Heap priority queue for order/restock urgency scheduling.

Three specialised heaps:
  1. OrderHeap    — ranks orders by urgency score (priority × age × value)
  2. RestockHeap  — ranks SKUs by stock depletion urgency
  3. ShipmentHeap — ranks in-transit shipments by delay risk

All heaps support O(log n) push/pop and O(1) peek.
"""

from __future__ import annotations
import heapq
import time
from dataclasses import dataclass, field
from typing import Dict, Generic, List, Optional, TypeVar
from enum import IntEnum


class PriorityWeight(IntEnum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


# ── Generic Priority Queue ────────────────────────────────────────────────────

T = TypeVar("T")

@dataclass(order=True)
class _PQEntry(Generic[T]):
    priority: float
    seq: int = field(compare=True)
    item: T = field(compare=False)


class PriorityQueue(Generic[T]):
    """
    Stable min-heap priority queue.
    Lower priority value = processed first (invert for max-heap via negation).
    Tie-broken by insertion sequence (FIFO within same priority).
    """

    def __init__(self):
        self._heap: List[_PQEntry] = []
        self._seq = 0
        self._entry_map: Dict[int, _PQEntry] = {}
        self._removed: set = set()

    def push(self, item: T, priority: float, item_id: int = None):
        entry = _PQEntry(priority=priority, seq=self._seq, item=item)
        self._seq += 1
        heapq.heappush(self._heap, entry)
        if item_id is not None:
            self._entry_map[item_id] = entry

    def pop(self) -> Optional[T]:
        while self._heap:
            entry = heapq.heappop(self._heap)
            if id(entry) not in self._removed:
                return entry.item
        return None

    def peek(self) -> Optional[T]:
        while self._heap:
            entry = self._heap[0]
            if id(entry) not in self._removed:
                return entry.item
            heapq.heappop(self._heap)
        return None

    def remove(self, item_id: int):
        """Lazy deletion — mark as removed, skip on pop."""
        if item_id in self._entry_map:
            self._removed.add(id(self._entry_map.pop(item_id)))

    def update_priority(self, item: T, new_priority: float, item_id: int):
        self.remove(item_id)
        self.push(item, new_priority, item_id)

    def __len__(self) -> int:
        return len(self._heap) - len(self._removed)

    def drain_top_k(self, k: int) -> List[T]:
        results = []
        for _ in range(k):
            item = self.pop()
            if item is None:
                break
            results.append(item)
        return results


# ── Order Urgency Heap ────────────────────────────────────────────────────────

@dataclass
class OrderUrgency:
    order_id: int
    order_number: str
    priority_label: str
    urgency_score: float
    days_overdue: float
    total_value: float
    status: str


class OrderHeap:
    """
    Ranks purchase/sales orders by composite urgency score.

    urgency = priority_weight × (1 + days_overdue)² × log(1 + total_value)

    Critical + 3 days late + $50k order → score ≈ 180  (pops first)
    Low      + 0 days late + $100 order → score ≈ 0.7   (pops last)
    """

    _PRIORITY_WEIGHTS = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}

    def __init__(self):
        self._pq: PriorityQueue[OrderUrgency] = PriorityQueue()

    def push_order(self, order_id: int, order_number: str, priority: str,
                   days_until_due: float, total_value: float, status: str):
        import math
        pw = self._PRIORITY_WEIGHTS.get(priority.lower(), 1.0)
        days_overdue = max(0.0, -days_until_due)
        score = pw * (1 + days_overdue) ** 2 * math.log1p(total_value)
        urgency = OrderUrgency(
            order_id=order_id,
            order_number=order_number,
            priority_label=priority,
            urgency_score=round(score, 4),
            days_overdue=days_overdue,
            total_value=total_value,
            status=status,
        )
        self._pq.push(urgency, -score, order_id)

    def pop_most_urgent(self) -> Optional[OrderUrgency]:
        return self._pq.pop()

    def top_k(self, k: int) -> List[OrderUrgency]:
        items = self._pq.drain_top_k(k)
        for item in items:
            self._pq.push(item, -item.urgency_score, item.order_id)
        return items

    def __len__(self):
        return len(self._pq)


# ── Restock Priority Heap ─────────────────────────────────────────────────────

@dataclass
class RestockUrgency:
    product_id: int
    sku: str
    name: str
    warehouse_id: int
    current_stock: int
    reorder_point: int
    avg_daily_demand: float
    days_until_stockout: float
    urgency_score: float


class RestockHeap:
    """
    Ranks SKUs by how soon they will stock out.

    days_to_stockout = current_stock / avg_daily_demand
    urgency_score    = 1 / (days_to_stockout + 0.1)   [higher = more urgent]

    A product with 0 stock and daily demand of 100 → urgency = 10
    A product with 500 stock and demand of 1      → urgency = 0.002
    """

    def __init__(self):
        self._pq: PriorityQueue[RestockUrgency] = PriorityQueue()

    def push_stock_entry(
        self,
        product_id: int, sku: str, name: str, warehouse_id: int,
        current_stock: int, reorder_point: int, avg_daily_demand: float,
    ):
        demand = max(avg_daily_demand, 0.01)
        days_out = current_stock / demand
        score = 1.0 / (days_out + 0.1)
        entry = RestockUrgency(
            product_id=product_id, sku=sku, name=name,
            warehouse_id=warehouse_id, current_stock=current_stock,
            reorder_point=reorder_point, avg_daily_demand=avg_daily_demand,
            days_until_stockout=round(days_out, 1),
            urgency_score=round(score, 6),
        )
        self._pq.push(entry, -score, product_id * 10_000 + warehouse_id)

    def top_k_critical(self, k: int = 20) -> List[RestockUrgency]:
        items = self._pq.drain_top_k(k)
        for item in items:
            self._pq.push(item, -item.urgency_score, item.product_id * 10_000 + item.warehouse_id)
        return items

    def __len__(self):
        return len(self._pq)


# ── Shipment Delay Risk Heap ──────────────────────────────────────────────────

@dataclass
class ShipmentRisk:
    shipment_id: int
    tracking_number: str
    carrier: str
    days_delayed: float
    risk_score: float
    status: str


class ShipmentRiskHeap:
    """Orders in-transit shipments by delay risk for proactive alerting."""

    def __init__(self):
        self._pq: PriorityQueue[ShipmentRisk] = PriorityQueue()

    def push_shipment(self, shipment_id: int, tracking_number: str,
                      carrier: str, expected_arrival_ts: float, status: str):
        now = time.time()
        days_delayed = max(0.0, (now - expected_arrival_ts) / 86400)
        risk_score = days_delayed ** 1.5
        entry = ShipmentRisk(
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            carrier=carrier,
            days_delayed=round(days_delayed, 2),
            risk_score=round(risk_score, 4),
            status=status,
        )
        self._pq.push(entry, -risk_score, shipment_id)

    def top_k_delayed(self, k: int = 10) -> List[ShipmentRisk]:
        items = self._pq.drain_top_k(k)
        for item in items:
            self._pq.push(item, -item.risk_score, item.shipment_id)
        return items
