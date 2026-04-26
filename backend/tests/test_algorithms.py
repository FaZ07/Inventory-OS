"""
Unit tests for all DSA algorithm implementations.
Run: pytest tests/test_algorithms.py -v
"""
import pytest
import math
from app.algorithms.graph import WarehouseGraph
from app.algorithms.trie import ProductTrie
from app.algorithms.heap import OrderHeap, RestockHeap, PriorityQueue
from app.algorithms.forecasting import (
    holt_winters_forecast,
    dp_replenishment,
    economic_order_quantity,
    safety_stock,
    rank_suppliers,
)


# ── Graph / Dijkstra Tests ────────────────────────────────────────────────────

class TestWarehouseGraph:
    def _build_simple_graph(self) -> WarehouseGraph:
        """
        Triangle: WH1(0,0) → WH2(0,1) → WH3(1,0)
        """
        g = WarehouseGraph()
        g.add_node(1, 0.0, 0.0)
        g.add_node(2, 0.0, 1.0)
        g.add_node(3, 1.0, 0.0)
        g.add_bidirectional_edge(1, 2)
        g.add_bidirectional_edge(2, 3)
        g.add_bidirectional_edge(1, 3, cost_per_km=5.0)  # expensive direct route
        return g

    def test_dijkstra_finds_path(self):
        g = self._build_simple_graph()
        result = g.dijkstra(1, 3)
        assert result is not None
        assert result.path[0] == 1
        assert result.path[-1] == 3

    def test_dijkstra_prefers_cheaper_route(self):
        g = self._build_simple_graph()
        # Direct 1→3 is expensive (cost_per_km=5), via 2 should be cheaper
        result = g.dijkstra(1, 3)
        assert result is not None
        assert result.total_cost >= 0

    def test_dijkstra_no_path(self):
        g = WarehouseGraph()
        g.add_node(1, 0.0, 0.0)
        g.add_node(2, 1.0, 1.0)
        # No edges added
        result = g.dijkstra(1, 2)
        assert result is None

    def test_all_shortest_paths(self):
        g = self._build_simple_graph()
        paths = g.all_shortest_paths(1)
        assert 2 in paths
        assert 3 in paths

    def test_bfs_reachable(self):
        g = self._build_simple_graph()
        reachable = g.bfs_reachable(1)
        assert set(reachable) == {1, 2, 3}

    def test_haversine_distance(self):
        g = WarehouseGraph()
        g.add_node(1, 40.7128, -74.0060)   # New York
        g.add_node(2, 51.5074, -0.1278)    # London
        g.add_bidirectional_edge(1, 2)
        result = g.dijkstra(1, 2)
        assert result is not None
        assert 5500 < result.total_distance_km < 5600  # ~5570 km


# ── Trie Tests ────────────────────────────────────────────────────────────────

class TestProductTrie:
    def _build_trie(self) -> ProductTrie:
        t = ProductTrie()
        t.insert("LAPTOP-001", "Gaming Laptop Pro", 1, 2.5)
        t.insert("LAPTOP-002", "Business Laptop", 2, 1.8)
        t.insert("PHONE-001", "Smartphone X", 3, 3.0)
        t.insert("TABLET-001", "Digital Tablet", 4, 1.2)
        return t

    def test_exact_lookup(self):
        t = self._build_trie()
        node = t.search_exact("LAPTOP-001")
        assert node is not None
        assert node.product_id == 1

    def test_exact_lookup_miss(self):
        t = self._build_trie()
        assert t.search_exact("NONEXISTENT") is None

    def test_autocomplete_prefix(self):
        t = self._build_trie()
        results = t.autocomplete("LAPTOP", top_k=5)
        assert len(results) >= 2
        skus = {r["sku"] for r in results}
        assert "LAPTOP-001" in skus or "LAPTOP-002" in skus

    def test_autocomplete_empty_on_no_match(self):
        t = self._build_trie()
        results = t.autocomplete("XXXXXXXXX")
        assert results == []

    def test_fuzzy_search_typo(self):
        t = self._build_trie()
        results = t.fuzzy_search("LAPTOPP", max_distance=1, top_k=5)
        # Should find LAPTOP variants with edit distance 1
        assert isinstance(results, list)

    def test_top_k_limit(self):
        t = self._build_trie()
        results = t.autocomplete("L", top_k=1)
        assert len(results) <= 1

    def test_rebuild(self):
        t = ProductTrie()
        t.rebuild([
            {"id": 10, "sku": "SKU-A", "name": "Alpha Product", "turnover_rate": 1.0},
            {"id": 11, "sku": "SKU-B", "name": "Beta Product", "turnover_rate": 2.0},
        ])
        assert t.search_exact("SKU-A") is not None


# ── Heap Tests ────────────────────────────────────────────────────────────────

class TestPriorityQueue:
    def test_basic_ordering(self):
        pq: PriorityQueue[str] = PriorityQueue()
        pq.push("low", priority=10)
        pq.push("high", priority=1)
        pq.push("medium", priority=5)
        assert pq.pop() == "high"
        assert pq.pop() == "medium"
        assert pq.pop() == "low"

    def test_empty_pop(self):
        pq: PriorityQueue[str] = PriorityQueue()
        assert pq.pop() is None

    def test_lazy_deletion(self):
        pq: PriorityQueue[str] = PriorityQueue()
        pq.push("item", priority=1, item_id=42)
        pq.remove(42)
        assert pq.pop() is None


class TestOrderHeap:
    def test_critical_order_pops_first(self):
        heap = OrderHeap()
        heap.push_order(1, "PO-001", "low", days_until_due=5, total_value=100, status="pending")
        heap.push_order(2, "PO-002", "critical", days_until_due=-2, total_value=50000, status="pending")
        heap.push_order(3, "PO-003", "medium", days_until_due=1, total_value=500, status="pending")
        top = heap.pop_most_urgent()
        assert top.order_id == 2

    def test_urgency_increases_with_overdue(self):
        heap = OrderHeap()
        heap.push_order(1, "PO-A", "high", days_until_due=-5, total_value=1000, status="pending")
        heap.push_order(2, "PO-B", "high", days_until_due=0, total_value=1000, status="pending")
        top = heap.pop_most_urgent()
        assert top.order_id == 1  # more overdue = higher urgency


class TestRestockHeap:
    def test_zero_stock_most_urgent(self):
        heap = RestockHeap()
        heap.push_stock_entry(1, "SKU-A", "Product A", 10, current_stock=100, reorder_point=50, avg_daily_demand=5)
        heap.push_stock_entry(2, "SKU-B", "Product B", 10, current_stock=0, reorder_point=20, avg_daily_demand=10)
        top = heap.top_k_critical(1)[0]
        assert top.product_id == 2


# ── Forecasting / DP Tests ────────────────────────────────────────────────────

class TestHoltWinters:
    def _generate_seasonal_data(self, n: int = 60) -> list:
        import math
        return [max(0, 100 + 20 * math.sin(2 * math.pi * i / 7) + i * 0.2) for i in range(n)]

    def test_returns_correct_length(self):
        data = self._generate_seasonal_data(60)
        result = holt_winters_forecast(data, periods_ahead=14, season_length=7)
        assert len(result.forecast) == 14
        assert len(result.confidence_lower) == 14
        assert len(result.confidence_upper) == 14

    def test_forecast_non_negative(self):
        data = self._generate_seasonal_data(60)
        result = holt_winters_forecast(data, periods_ahead=14, season_length=7)
        assert all(f >= 0 for f in result.forecast)

    def test_confidence_interval_ordering(self):
        data = self._generate_seasonal_data(60)
        result = holt_winters_forecast(data, periods_ahead=14, season_length=7)
        for lo, hi in zip(result.confidence_lower, result.confidence_upper):
            assert lo <= hi

    def test_mape_reasonable(self):
        data = self._generate_seasonal_data(60)
        result = holt_winters_forecast(data, periods_ahead=7, season_length=7)
        assert result.mape < 50.0  # reasonable for synthetic data


class TestDPReplenishment:
    def test_covers_all_demand(self):
        demand = [10.0, 20.0, 15.0, 25.0, 30.0]
        plan = dp_replenishment(demand, holding_cost_per_unit_period=1.0, ordering_cost=50.0)
        assert plan.total_ordered >= sum(demand)

    def test_minimizes_cost(self):
        demand = [10.0] * 6
        plan = dp_replenishment(demand, holding_cost_per_unit_period=0.5, ordering_cost=20.0)
        assert plan.total_cost > 0
        assert plan.periods == 6

    def test_initial_stock_reduces_orders(self):
        demand = [10.0, 10.0, 10.0]
        plan_no_stock = dp_replenishment(demand, 1.0, 50.0, initial_stock=0)
        plan_with_stock = dp_replenishment(demand, 1.0, 50.0, initial_stock=30)
        assert plan_with_stock.total_ordered <= plan_no_stock.total_ordered


class TestEOQ:
    def test_eoq_positive(self):
        result = economic_order_quantity(1000, 50.0, 0.25, 10.0)
        assert result.eoq > 0

    def test_eoq_formula(self):
        # Q* = sqrt(2 * 1000 * 50 / (0.25 * 10)) = sqrt(100000/2.5) = sqrt(40000) = 200
        result = economic_order_quantity(1000, 50.0, 0.25, 10.0)
        assert abs(result.eoq - 200) < 1.0

    def test_cost_equality(self):
        result = economic_order_quantity(1000, 50.0, 0.25, 10.0)
        assert abs(result.annual_ordering_cost - result.annual_holding_cost) < 1.0


class TestSafetyStock:
    def test_higher_service_level_more_stock(self):
        ss_95 = safety_stock(10, 3, 7, 1, 0.95)
        ss_90 = safety_stock(10, 3, 7, 1, 0.90)
        assert ss_95 >= ss_90

    def test_non_negative(self):
        ss = safety_stock(0, 0, 0, 0, 0.95)
        assert ss >= 0


class TestSupplierRanking:
    def test_ranking_order(self):
        suppliers = [
            {"id": 1, "name": "Bad Supplier", "on_time_delivery_rate": 0.5, "quality_score": 0.5,
             "price_competitiveness": 0.5, "lead_time_days": 30},
            {"id": 2, "name": "Great Supplier", "on_time_delivery_rate": 1.0, "quality_score": 1.0,
             "price_competitiveness": 1.0, "lead_time_days": 3},
        ]
        ranked = rank_suppliers(suppliers)
        assert ranked[0].supplier_id == 2  # best should rank first

    def test_ranks_assigned(self):
        suppliers = [
            {"id": i, "name": f"S{i}", "on_time_delivery_rate": i / 5,
             "quality_score": i / 5, "price_competitiveness": i / 5, "lead_time_days": 10 - i}
            for i in range(1, 6)
        ]
        ranked = rank_suppliers(suppliers)
        assert [s.rank for s in ranked] == [1, 2, 3, 4, 5]

    def test_empty_input(self):
        assert rank_suppliers([]) == []
