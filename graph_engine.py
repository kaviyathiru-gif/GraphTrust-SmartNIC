"""
Lightweight Graph Engine (Pure Python / NumPy).
Provides trust-weighted Dijkstra shortest path and EigenTrust/PageRank power iteration.
Runs out of the box with zero third-party graph dependencies.
"""
import heapq
from typing import Dict, List, Optional, Tuple, Set

class SimpleGraph:
    def __init__(self, directed: bool = False):
        self.directed = directed
        self.nodes: Dict[str, Dict] = {}
        self.adj: Dict[str, Dict[str, float]] = {}

    def add_node(self, node_id: str, **attrs):
        if node_id not in self.nodes:
            self.nodes[node_id] = {}
            self.adj[node_id] = {}
        self.nodes[node_id].update(attrs)

    def add_edge(self, u: str, v: str, weight: float = 1.0, **attrs):
        self.add_node(u)
        self.add_node(v)
        self.adj[u][v] = weight
        if not self.directed:
            self.adj[v][u] = weight

    def neighbors(self, u: str) -> List[str]:
        return list(self.adj.get(u, {}).keys())

    def shortest_path(self, source: str, target: str, excluded_nodes: Optional[Set[str]] = None) -> Optional[List[str]]:
        """Dijkstra's shortest path avoiding excluded nodes."""
        if excluded_nodes is None:
            excluded_nodes = set()
        if source in excluded_nodes or target in excluded_nodes:
            return None
        if source not in self.adj or target not in self.adj:
            return None
        if source == target:
            return [source]

        dist = {source: 0.0}
        prev = {}
        pq = [(0.0, source)]
        visited = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u == target:
                break
            if u in visited or u in excluded_nodes:
                continue
            visited.add(u)

            for v, weight in self.adj.get(u, {}).items():
                if v in excluded_nodes:
                    continue
                new_dist = d + weight
                if v not in dist or new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if target not in prev and source != target:
            return None

        path = []
        curr = target
        while curr:
            path.append(curr)
            curr = prev.get(curr)
        path.reverse()
        return path

    def pagerank(self, alpha: float = 0.85, max_iter: int = 50, tol: float = 1e-6,
                 personalization: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """EigenTrust / PageRank calculation via Power Iteration."""
        nodes = list(self.nodes.keys())
        N = len(nodes)
        if N == 0:
            return {}

        if personalization is None:
            p = {n: 1.0 / N for n in nodes}
        else:
            total = sum(personalization.get(n, 0.0) for n in nodes)
            p = {n: personalization.get(n, 0.0) / total if total > 0 else 1.0 / N for n in nodes}

        ranks = {n: 1.0 / N for n in nodes}

        for _ in range(max_iter):
            next_ranks = {n: (1.0 - alpha) * p[n] for n in nodes}
            dangling_sum = 0.0

            for u in nodes:
                out_edges = self.adj.get(u, {})
                out_weight_sum = sum(out_edges.values())
                if out_weight_sum == 0:
                    dangling_sum += ranks[u]
                else:
                    for v, w in out_edges.items():
                        next_ranks[v] += alpha * ranks[u] * (w / out_weight_sum)

            for n in nodes:
                next_ranks[n] += alpha * dangling_sum * p[n]

            err = sum(abs(next_ranks[n] - ranks[n]) for n in nodes)
            ranks = next_ranks
            if err < tol:
                break

        return ranks
