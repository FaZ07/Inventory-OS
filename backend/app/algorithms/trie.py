"""
Trie (Prefix Tree) for O(k) SKU/product search and autocomplete.

Where k = length of the query prefix — far faster than ILIKE on large
product catalogs. Also handles ranked retrieval by frequency score.

Time:  insert O(k), search O(k + output_size)
Space: O(ALPHABET_SIZE × total_chars) ≈ O(n·k) in practice
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_end: bool = False
    product_id: Optional[int] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    frequency: int = 0
    score: float = 0.0


class ProductTrie:
    """
    Compressed prefix trie over product SKUs and names.
    Supports:
      - Exact lookup
      - Prefix autocomplete (top-k by frequency/score)
      - Fuzzy match (edit distance ≤ 1 via neighbourhood expansion)
    """

    def __init__(self):
        self._root = TrieNode()
        self._total_inserts = 0

    # ── Insert ────────────────────────────────────────────────────────────────

    def insert(self, sku: str, name: str, product_id: int, score: float = 1.0):
        """Index a product by both SKU and normalised name tokens."""
        self._insert_word(sku.upper(), sku, name, product_id, score)
        for token in self._tokenise(name):
            self._insert_word(token, sku, name, product_id, score)
        self._total_inserts += 1

    def _insert_word(self, word: str, sku: str, name: str, product_id: int, score: float):
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.product_id = product_id
        node.sku = sku
        node.name = name
        node.frequency += 1
        node.score = score

    # ── Search ────────────────────────────────────────────────────────────────

    def search_exact(self, query: str) -> Optional[TrieNode]:
        """O(k) exact lookup. Returns terminal node or None."""
        node = self._root
        for ch in query.upper():
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node if node.is_end else None

    def autocomplete(self, prefix: str, top_k: int = 10) -> List[dict]:
        """
        Return up to top_k products whose SKU/name starts with prefix.
        Results ranked by (frequency × score) descending.
        """
        node = self._root
        for ch in prefix.upper():
            if ch not in node.children:
                return []
            node = node.children[ch]

        results: List[Tuple[float, dict]] = []
        self._dfs_collect(node, results)
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]

    def fuzzy_search(self, query: str, max_distance: int = 1, top_k: int = 10) -> List[dict]:
        """
        Levenshtein-bounded search. Explores the trie with a running edit
        distance array (DP row) to prune branches early.
        Time: O(k × SIGMA × n) worst-case but heavily pruned in practice.
        """
        query = query.upper()
        current_row = list(range(len(query) + 1))
        results: List[Tuple[int, dict]] = []

        for ch, child in self._root.children.items():
            self._fuzzy_dfs(child, ch, query, current_row, max_distance, results)

        results.sort(key=lambda x: x[0])
        seen: set[int] = set()
        deduped = []
        for dist, item in results:
            if item["product_id"] not in seen:
                seen.add(item["product_id"])
                deduped.append({**item, "edit_distance": dist})
        return deduped[:top_k]

    def _fuzzy_dfs(self, node: TrieNode, letter: str, query: str,
                   prev_row: List[int], max_dist: int, results: list):
        n = len(query)
        current_row = [prev_row[0] + 1]
        for col in range(1, n + 1):
            insert_cost = current_row[col - 1] + 1
            delete_cost = prev_row[col] + 1
            replace_cost = prev_row[col - 1] + (0 if query[col - 1] == letter else 1)
            current_row.append(min(insert_cost, delete_cost, replace_cost))

        if current_row[n] <= max_dist and node.is_end and node.product_id is not None:
            results.append((current_row[n], {
                "product_id": node.product_id,
                "sku": node.sku,
                "name": node.name,
                "score": node.score,
            }))

        if min(current_row) <= max_dist:
            for ch, child in node.children.items():
                self._fuzzy_dfs(child, ch, query, current_row, max_dist, results)

    def _dfs_collect(self, node: TrieNode, results: List[Tuple[float, dict]]):
        if node.is_end and node.product_id is not None:
            rank = node.frequency * node.score
            results.append((rank, {
                "product_id": node.product_id,
                "sku": node.sku,
                "name": node.name,
                "frequency": node.frequency,
                "score": node.score,
            }))
        for child in node.children.values():
            self._dfs_collect(child, results)

    def increment_frequency(self, sku: str):
        """Call on each product search hit to boost result ranking."""
        node = self._root
        for ch in sku.upper():
            if ch not in node.children:
                return
            node = node.children[ch]
        if node.is_end:
            node.frequency += 1

    def rebuild(self, products: list):
        """Full rebuild from a list of product dicts."""
        self._root = TrieNode()
        self._total_inserts = 0
        for p in products:
            pid = p["id"] if isinstance(p, dict) else p.id
            sku = p["sku"] if isinstance(p, dict) else p.sku
            name = p["name"] if isinstance(p, dict) else p.name
            score = float(p.get("turnover_rate", 1.0) if isinstance(p, dict) else getattr(p, "turnover_rate", 1.0))
            self.insert(sku, name, pid, score)

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return [t.upper() for t in text.split() if len(t) >= 2]

    @property
    def size(self) -> int:
        return self._total_inserts


# Module-level singleton (rebuilt on demand by search service)
_product_trie: Optional[ProductTrie] = None


def get_trie() -> ProductTrie:
    global _product_trie
    if _product_trie is None:
        _product_trie = ProductTrie()
    return _product_trie


def rebuild_trie(products: list):
    global _product_trie
    _product_trie = ProductTrie()
    _product_trie.rebuild(products)
