"""
Comprehensive Graph Algorithms implementation for DSA-II PBL requirements.
Includes DFS, BFS, Transitive Closure (Warshall), Kruskal's MST (DSU),
Prim's MST, Dijkstra, Bellman-Ford, and Floyd-Warshall.
"""

import time
import heapq
from typing import Dict, List, Tuple, Set, Optional, Any
from app.graph_structure import Graph


# ==========================================================
# Disjoint Set Union (DSU / Union-Find) for Kruskal's MST
# DSA Concept: Path Compression + Union by Rank
# Time: O(alpha(V)) near-constant amortized time
# ==========================================================

class DisjointSetUnion:
    """Disjoint Set Union with Path Compression and Union by Rank."""

    def __init__(self, elements: List[str]):
        self.parent: Dict[str, str] = {x: x for x in elements}
        self.rank: Dict[str, int] = {x: 0 for x in elements}

    def find(self, x: str) -> str:
        """Find representative with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        """Union sets containing x and y. Returns True if merged, False if cycle."""
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False  # Already in same set (would create cycle)

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        return True


class GraphAlgorithms:
    """Collection of DSA-II graph algorithms."""

    # ------------------------------------------------------
    # A. Depth-First Search (DFS)
    # ------------------------------------------------------
    @staticmethod
    def dfs_traversal(graph: Graph, start_vertex: Optional[str] = None) -> Dict[str, Any]:
        """
        DFS traversal exploring all connected components.
        Time: O(V + E), Auxiliary Space: O(V)
        """
        start_time = time.perf_counter()
        visited: Set[str] = set()
        traversal_order: List[str] = []
        components: List[List[str]] = []

        vertices = graph.get_vertices()
        if not vertices:
            return {
                "algorithm": "DFS",
                "traversal_order": [],
                "components": [],
                "component_count": 0,
                "vertex_count": 0,
                "edge_count": 0,
                "execution_time_ms": 0.0,
            }

        # If start vertex provided, explore its component first
        ordered_starts = []
        if start_vertex and start_vertex in graph.adj:
            ordered_starts.append(start_vertex)
        for v in sorted(vertices):
            if v not in ordered_starts:
                ordered_starts.append(v)

        def _dfs_visit(u: str, current_comp: List[str]):
            visited.add(u)
            traversal_order.append(u)
            current_comp.append(u)
            for neighbor, _ in sorted(graph.get_neighbors(u), key=lambda x: x[0]):
                if neighbor not in visited:
                    _dfs_visit(neighbor, current_comp)

        for v in ordered_starts:
            if v not in visited:
                comp: List[str] = []
                _dfs_visit(v, comp)
                components.append(comp)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Depth-First Search (DFS)",
            "traversal_order": traversal_order,
            "components": components,
            "component_count": len(components),
            "vertex_count": graph.vertex_count(),
            "edge_count": graph.edge_count(),
            "execution_time_ms": elapsed_ms,
        }

    # ------------------------------------------------------
    # B. Breadth-First Search (BFS)
    # ------------------------------------------------------
    @staticmethod
    def bfs_traversal(graph: Graph, start_vertex: Optional[str] = None) -> Dict[str, Any]:
        """
        BFS traversal level-by-level using a FIFO queue.
        Time: O(V + E), Auxiliary Space: O(V)
        """
        start_time = time.perf_counter()
        visited: Set[str] = set()
        traversal_order: List[str] = []
        components: List[List[str]] = []
        levels: Dict[str, int] = {}

        vertices = graph.get_vertices()
        if not vertices:
            return {
                "algorithm": "BFS",
                "traversal_order": [],
                "components": [],
                "component_count": 0,
                "levels": {},
                "vertex_count": 0,
                "edge_count": 0,
                "execution_time_ms": 0.0,
            }

        ordered_starts = []
        if start_vertex and start_vertex in graph.adj:
            ordered_starts.append(start_vertex)
        for v in sorted(vertices):
            if v not in ordered_starts:
                ordered_starts.append(v)

        for v in ordered_starts:
            if v not in visited:
                comp: List[str] = []
                queue: List[str] = [v]
                visited.add(v)
                levels[v] = 0

                while queue:
                    u = queue.pop(0)
                    traversal_order.append(u)
                    comp.append(u)

                    for neighbor, _ in sorted(graph.get_neighbors(u), key=lambda x: x[0]):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            levels[neighbor] = levels[u] + 1
                            queue.append(neighbor)

                components.append(comp)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Breadth-First Search (BFS)",
            "traversal_order": traversal_order,
            "components": components,
            "component_count": len(components),
            "levels": levels,
            "vertex_count": graph.vertex_count(),
            "edge_count": graph.edge_count(),
            "execution_time_ms": elapsed_ms,
        }

    # ------------------------------------------------------
    # C. Transitive Closure (Warshall's Algorithm)
    # ------------------------------------------------------
    @staticmethod
    def transitive_closure_warshall(graph: Graph) -> Dict[str, Any]:
        """
        Warshall's Algorithm for Reachability Matrix.
        R[i][j] = 1 if there is a path from i to j, else 0.
        Recurrence: R^(k)[i][j] = R^(k-1)[i][j] OR (R^(k-1)[i][k] AND R^(k-1)[k][j])
        Time: O(V^3), Space: O(V^2). Designed for small-to-moderate graphs.
        """
        start_time = time.perf_counter()
        vertices = sorted(graph.get_vertices())
        n = len(vertices)
        v_idx = {v: i for i, v in enumerate(vertices)}

        # Initialize matrix: R[i][i] = 1, R[i][j] = 1 if edge exists
        matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1

        for u in vertices:
            u_i = v_idx[u]
            for v, _ in graph.get_neighbors(u):
                v_j = v_idx[v]
                matrix[u_i][v_j] = 1

        # Warshall's 3 nested loops
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    matrix[i][j] = matrix[i][j] or (matrix[i][k] and matrix[k][j])

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Warshall's Transitive Closure",
            "vertices": vertices,
            "matrix": matrix,
            "vertex_count": n,
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O(V^3), Space: O(V^2)",
        }

    # ------------------------------------------------------
    # D. Kruskal's Minimum Spanning Tree
    # ------------------------------------------------------
    @staticmethod
    def kruskal_mst(graph: Graph) -> Dict[str, Any]:
        """
        Kruskal's Algorithm using Disjoint Set Union (Union-Find).
        Sorts edges by weight, merges disjoint sets avoiding cycles.
        Yields Minimum Spanning Forest (MSF) if graph is disconnected.
        Time: O(E log E)
        """
        start_time = time.perf_counter()
        vertices = graph.get_vertices()
        edges = graph.get_edges()

        # Sort edges by weight
        sorted_edges = sorted(edges, key=lambda e: e[2])
        dsu = DisjointSetUnion(vertices)

        mst_edges: List[Tuple[str, str, float]] = []
        total_weight = 0.0

        for u, v, w in sorted_edges:
            if dsu.union(u, v):
                mst_edges.append((u, v, w))
                total_weight += w

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Kruskal's Minimum Spanning Tree",
            "mst_edges": mst_edges,
            "total_weight": total_weight,
            "edge_count": len(mst_edges),
            "original_edge_count": len(edges),
            "vertex_count": len(vertices),
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O(E log E), Space: O(V)",
        }

    # ------------------------------------------------------
    # E. Prim's Minimum Spanning Tree
    # ------------------------------------------------------
    @staticmethod
    def prim_mst(graph: Graph, start_vertex: Optional[str] = None) -> Dict[str, Any]:
        """
        Prim's Algorithm using Min-Heap priority queue.
        Starts at start_vertex, greedily adds lowest weight incident edge to unvisited vertex.
        Time: O(E log V)
        """
        start_time = time.perf_counter()
        vertices = graph.get_vertices()
        if not vertices:
            return {
                "algorithm": "Prim's Minimum Spanning Tree",
                "mst_edges": [],
                "total_weight": 0.0,
                "execution_time_ms": 0.0,
            }

        start = start_vertex if (start_vertex and start_vertex in graph.adj) else vertices[0]
        visited: Set[str] = {start}
        mst_edges: List[Tuple[str, str, float]] = []
        total_weight = 0.0

        # Min-heap stores: (weight, u, v)
        pq: List[Tuple[float, str, str]] = []
        for v, w in graph.get_neighbors(start):
            heapq.heappush(pq, (w, start, v))

        while pq and len(visited) < len(vertices):
            w, u, v = heapq.heappop(pq)
            if v in visited:
                continue

            visited.add(v)
            mst_edges.append((u, v, w))
            total_weight += w

            for neighbor, next_w in graph.get_neighbors(v):
                if neighbor not in visited:
                    heapq.heappush(pq, (next_w, v, neighbor))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Prim's Minimum Spanning Tree",
            "start_vertex": start,
            "mst_edges": mst_edges,
            "total_weight": total_weight,
            "edge_count": len(mst_edges),
            "vertex_count": len(vertices),
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O(E log V), Space: O(V + E)",
        }

    # ------------------------------------------------------
    # F. Dijkstra's Shortest Path
    # ------------------------------------------------------
    @staticmethod
    def dijkstra_shortest_path(
        graph: Graph,
        source: str,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dijkstra's Single-Source Shortest Path using Min-Heap.
        Weights must be non-negative.
        Time: O((V + E) log V)
        """
        start_time = time.perf_counter()
        if source not in graph.adj:
            raise ValueError(f"Source vertex '{source}' not in graph.")

        distances: Dict[str, float] = {v: float("inf") for v in graph.get_vertices()}
        predecessors: Dict[str, Optional[str]] = {v: None for v in graph.get_vertices()}
        distances[source] = 0.0

        # Heap items: (distance, vertex)
        pq: List[Tuple[float, str]] = [(0.0, source)]

        while pq:
            curr_dist, u = heapq.heappop(pq)
            if curr_dist > distances[u]:
                continue

            if target and u == target:
                break

            for v, weight in graph.get_neighbors(u):
                if weight < 0:
                    raise ValueError(f"Dijkstra encountered negative edge weight ({u}->{v}: {weight}).")
                new_dist = curr_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(pq, (new_dist, v))

        # Reconstruct path if target specified
        path: List[str] = []
        target_dist = distances.get(target, float("inf")) if target else None

        if target and target in predecessors and distances[target] < float("inf"):
            curr: Optional[str] = target
            while curr is not None:
                path.append(curr)
                curr = predecessors[curr]
            path.reverse()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Dijkstra's Shortest Path",
            "source": source,
            "target": target,
            "shortest_path": path if target else None,
            "target_distance": target_dist,
            "all_distances": distances,
            "predecessors": predecessors,
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O((V + E) log V), Space: O(V)",
        }

    # ------------------------------------------------------
    # G. Bellman-Ford Algorithm
    # ------------------------------------------------------
    @staticmethod
    def bellman_ford(graph: Graph, source: str) -> Dict[str, Any]:
        """
        Bellman-Ford Shortest Path with Negative Cycle Detection.
        Relaxes edges |V|-1 times, then checks for negative cycles on |V|-th pass.
        Time: O(V * E)
        """
        start_time = time.perf_counter()
        vertices = graph.get_vertices()
        if source not in graph.adj:
            raise ValueError(f"Source vertex '{source}' not in graph.")

        distances: Dict[str, float] = {v: float("inf") for v in vertices}
        predecessors: Dict[str, Optional[str]] = {v: None for v in vertices}
        distances[source] = 0.0

        # Extract all directed edges
        edges: List[Tuple[str, str, float]] = []
        for u in graph.adj:
            for v, w in graph.adj[u]:
                edges.append((u, v, w))

        V = len(vertices)

        # Relax all edges |V| - 1 times
        for _ in range(V - 1):
            updated = False
            for u, v, w in edges:
                if distances[u] != float("inf") and distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w
                    predecessors[v] = u
                    updated = True
            if not updated:
                break

        # Check for negative-weight cycles
        has_negative_cycle = False
        negative_cycle_edges: List[Tuple[str, str, float]] = []
        for u, v, w in edges:
            if distances[u] != float("inf") and distances[u] + w < distances[v]:
                has_negative_cycle = True
                negative_cycle_edges.append((u, v, w))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Bellman-Ford",
            "source": source,
            "distances": distances,
            "predecessors": predecessors,
            "has_negative_cycle": has_negative_cycle,
            "negative_cycle_edges": negative_cycle_edges,
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O(V * E), Space: O(V)",
        }

    # ------------------------------------------------------
    # H. Floyd-Warshall Algorithm
    # ------------------------------------------------------
    @staticmethod
    def floyd_warshall(graph: Graph) -> Dict[str, Any]:
        """
        Floyd-Warshall All-Pairs Shortest Path algorithm.
        D[i][j] = min(D[i][j], D[i][k] + D[k][j])
        Time: O(V^3), Space: O(V^2)
        """
        start_time = time.perf_counter()
        vertices = sorted(graph.get_vertices())
        n = len(vertices)
        v_idx = {v: i for i, v in enumerate(vertices)}

        # Initialize matrix: dist[i][i] = 0, dist[i][j] = weight or inf
        dist = [[float("inf")] * n for _ in range(n)]
        for i in range(n):
            dist[i][i] = 0.0

        for u in graph.adj:
            u_i = v_idx[u]
            for v, w in graph.adj[u]:
                v_j = v_idx[v]
                dist[u_i][v_j] = min(dist[u_i][v_j], w)

        # 3 nested loops
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]

        # Check for negative cycles
        has_negative_cycle = any(dist[i][i] < 0 for i in range(n))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Floyd-Warshall All-Pairs Shortest Path",
            "vertices": vertices,
            "distance_matrix": dist,
            "has_negative_cycle": has_negative_cycle,
            "vertex_count": n,
            "execution_time_ms": elapsed_ms,
            "complexity": "Time: O(V^3), Space: O(V^2)",
        }
