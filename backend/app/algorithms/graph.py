"""
Graph-based route optimization using Dijkstra's algorithm.

Models the warehouse network as a weighted directed graph where:
  - Nodes = warehouses (indexed by warehouse ID)
  - Edges = shipping lanes with cost/distance weights
  - Goal  = find cheapest/shortest path between any two warehouses

Time:  O((V + E) log V)  using a binary min-heap
Space: O(V + E)
"""

from __future__ import annotations
import heapq
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Edge:
    to: int
    distance_km: float
    cost_per_km: float
    transit_days: float

    @property
    def weight(self) -> float:
        return self.distance_km * self.cost_per_km


@dataclass(order=True)
class _HeapEntry:
    cost: float
    node: int = field(compare=False)
    path: List[int] = field(compare=False, default_factory=list)


class WarehouseGraph:
    """Weighted directed graph over the warehouse network."""

    def __init__(self):
        self._adj: Dict[int, List[Edge]] = {}
        self._node_coords: Dict[int, Tuple[float, float]] = {}

    # ── Construction ──────────────────────────────────────────────────────────

    def add_node(self, warehouse_id: int, lat: float, lon: float):
        if warehouse_id not in self._adj:
            self._adj[warehouse_id] = []
        self._node_coords[warehouse_id] = (lat, lon)

    def add_edge(self, from_id: int, to_id: int, cost_per_km: float = 0.85, transit_days: float = 1.0):
        """Add a directed shipping lane. Distance is computed from coordinates."""
        dist = self._haversine(from_id, to_id)
        self._adj.setdefault(from_id, []).append(Edge(to_id, dist, cost_per_km, transit_days))

    def add_bidirectional_edge(self, a: int, b: int, cost_per_km: float = 0.85, transit_days: float = 1.0):
        self.add_edge(a, b, cost_per_km, transit_days)
        self.add_edge(b, a, cost_per_km, transit_days)

    def build_from_warehouses(self, warehouses: list, full_mesh: bool = True):
        """
        Populate graph from a list of warehouse dicts/objects.
        If full_mesh=True, create lanes between every pair (O(n²) edges).
        """
        for wh in warehouses:
            wid = wh["id"] if isinstance(wh, dict) else wh.id
            lat = wh["latitude"] if isinstance(wh, dict) else wh.latitude
            lon = wh["longitude"] if isinstance(wh, dict) else wh.longitude
            self.add_node(wid, lat, lon)

        ids = list(self._adj.keys())
        if full_mesh:
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    self.add_bidirectional_edge(a, b)

    # ── Dijkstra's Shortest Path ──────────────────────────────────────────────

    def dijkstra(self, source: int, target: int) -> Optional[RouteResult]:
        """
        Returns the minimum-cost route from source → target.
        Returns None if no path exists.
        """
        if source not in self._adj or target not in self._adj:
            return None

        dist: Dict[int, float] = {node: math.inf for node in self._adj}
        dist[source] = 0.0
        prev: Dict[int, Optional[int]] = {node: None for node in self._adj}
        visited: set = set()

        heap: List[_HeapEntry] = [_HeapEntry(0.0, source)]

        while heap:
            entry = heapq.heappop(heap)
            u = entry.node

            if u in visited:
                continue
            visited.add(u)

            if u == target:
                break

            for edge in self._adj.get(u, []):
                v = edge.to
                alt = dist[u] + edge.weight
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, _HeapEntry(alt, v))

        if dist[target] == math.inf:
            return None

        path = self._reconstruct_path(prev, source, target)
        total_km = self._path_distance(path)
        total_days = self._path_transit_days(path)

        return RouteResult(
            path=path,
            total_cost=dist[target],
            total_distance_km=total_km,
            estimated_days=total_days,
        )

    def all_shortest_paths(self, source: int) -> Dict[int, "RouteResult"]:
        """Dijkstra from one source to all reachable nodes."""
        if source not in self._adj:
            return {}

        dist: Dict[int, float] = {node: math.inf for node in self._adj}
        dist[source] = 0.0
        prev: Dict[int, Optional[int]] = {node: None for node in self._adj}
        visited: set = set()

        heap = [_HeapEntry(0.0, source)]

        while heap:
            entry = heapq.heappop(heap)
            u = entry.node
            if u in visited:
                continue
            visited.add(u)

            for edge in self._adj.get(u, []):
                v = edge.to
                alt = dist[u] + edge.weight
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, _HeapEntry(alt, v))

        results: Dict[int, RouteResult] = {}
        for target in self._adj:
            if target == source or dist[target] == math.inf:
                continue
            path = self._reconstruct_path(prev, source, target)
            results[target] = RouteResult(
                path=path,
                total_cost=dist[target],
                total_distance_km=self._path_distance(path),
                estimated_days=self._path_transit_days(path),
            )
        return results

    def bfs_reachable(self, source: int) -> List[int]:
        """BFS to find all warehouse IDs reachable from source."""
        visited, queue = {source}, [source]
        head = 0
        while head < len(queue):
            node = queue[head]; head += 1
            for edge in self._adj.get(node, []):
                if edge.to not in visited:
                    visited.add(edge.to)
                    queue.append(edge.to)
        return list(visited)

    def find_bottlenecks(self) -> List[int]:
        """
        Identify bridge nodes (articulation points) using iterative DFS.
        Removing these warehouses would disconnect the network — high-risk nodes.
        """
        n = len(self._adj)
        nodes = list(self._adj.keys())
        index_of = {nid: i for i, nid in enumerate(nodes)}
        disc = [-1] * n
        low = [-1] * n
        visited = [False] * n
        ap_set: set[int] = set()
        timer = [0]

        def dfs(u_idx: int, parent: int):
            visited[u_idx] = True
            disc[u_idx] = low[u_idx] = timer[0]
            timer[0] += 1
            children = 0
            for edge in self._adj.get(nodes[u_idx], []):
                v_idx = index_of.get(edge.to, -1)
                if v_idx == -1:
                    continue
                if not visited[v_idx]:
                    children += 1
                    dfs(v_idx, u_idx)
                    low[u_idx] = min(low[u_idx], low[v_idx])
                    if parent == -1 and children > 1:
                        ap_set.add(nodes[u_idx])
                    if parent != -1 and low[v_idx] >= disc[u_idx]:
                        ap_set.add(nodes[u_idx])
                elif v_idx != parent:
                    low[u_idx] = min(low[u_idx], disc[v_idx])

        for i in range(n):
            if not visited[i]:
                dfs(i, -1)

        return list(ap_set)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _haversine(self, a: int, b: int) -> float:
        """Great-circle distance in km between two warehouse nodes."""
        lat1, lon1 = self._node_coords[a]
        lat2, lon2 = self._node_coords[b]
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a_val = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a_val))

    def _reconstruct_path(self, prev: Dict[int, Optional[int]], source: int, target: int) -> List[int]:
        path = []
        cur: Optional[int] = target
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path if path[0] == source else []

    def _path_distance(self, path: List[int]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            total += self._haversine(path[i], path[i + 1])
        return round(total, 2)

    def _path_transit_days(self, path: List[int]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            for edge in self._adj.get(path[i], []):
                if edge.to == path[i + 1]:
                    total += edge.transit_days
                    break
        return round(total, 1)


@dataclass
class RouteResult:
    path: List[int]
    total_cost: float
    total_distance_km: float
    estimated_days: float

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "total_cost": round(self.total_cost, 2),
            "total_distance_km": self.total_distance_km,
            "estimated_days": self.estimated_days,
            "hops": len(self.path) - 1,
        }
