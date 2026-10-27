"""
Tests for Graph Data Structure and DSA-II Graph Algorithms.
Covers Requirements:
8. DFS connected components
9. BFS connected components
10. Disconnected graph handling
11. Kruskal's MST on a connected graph
12. Prim's MST on a connected graph
13. Dijkstra's shortest path
14. Bellman-Ford negative-cycle detection
15. Floyd-Warshall distance calculation
"""

import unittest
from app.graph_structure import Graph
from app.graph_algorithms import GraphAlgorithms, DisjointSetUnion


class TestGraphAlgorithms(unittest.TestCase):
    def test_08_and_10_dfs_connected_components_and_disconnected(self):
        """Test 8 & 10: DFS discovery of connected components on disconnected graph."""
        g = Graph(directed=False)
        # Component 1: A - B - C
        g.add_edge("A", "B", 1.0)
        g.add_edge("B", "C", 1.0)
        # Component 2: D - E
        g.add_edge("D", "E", 1.0)
        # Component 3: Isolated vertex F
        g.add_vertex("F")

        res = GraphAlgorithms.dfs_traversal(g, start_vertex="A")

        self.assertEqual(res["component_count"], 3)
        self.assertEqual(res["vertex_count"], 6)

        # First component should contain {A, B, C}
        comp_sets = [set(c) for c in res["components"]]
        self.assertIn({"A", "B", "C"}, comp_sets)
        self.assertIn({"D", "E"}, comp_sets)
        self.assertIn({"F"}, comp_sets)

    def test_09_bfs_traversal_and_levels(self):
        """Test 9: BFS level-by-level traversal."""
        g = Graph(directed=False)
        # Root A, children B & C, grandchild D connected to B
        g.add_edge("A", "B", 1.0)
        g.add_edge("A", "C", 1.0)
        g.add_edge("B", "D", 1.0)

        res = GraphAlgorithms.bfs_traversal(g, start_vertex="A")

        self.assertEqual(res["component_count"], 1)
        self.assertEqual(res["levels"]["A"], 0)
        self.assertEqual(res["levels"]["B"], 1)
        self.assertEqual(res["levels"]["C"], 1)
        self.assertEqual(res["levels"]["D"], 2)

    def test_11_kruskal_mst(self):
        """Test 11: Kruskal's Minimum Spanning Tree with Union-Find."""
        g = Graph(directed=False)
        # Standard textbook triangle with chord
        g.add_edge("1", "2", 1.0)
        g.add_edge("2", "3", 2.0)
        g.add_edge("1", "3", 4.0)
        g.add_edge("3", "4", 1.0)

        res = GraphAlgorithms.kruskal_mst(g)

        self.assertEqual(res["edge_count"], 3)  # V - 1 = 4 - 1 = 3 edges
        self.assertEqual(res["total_weight"], 4.0)  # 1.0 + 1.0 + 2.0 = 4.0

    def test_12_prim_mst(self):
        """Test 12: Prim's Minimum Spanning Tree with Priority Queue."""
        g = Graph(directed=False)
        g.add_edge("A", "B", 3.0)
        g.add_edge("A", "C", 1.0)
        g.add_edge("B", "C", 2.0)
        g.add_edge("C", "D", 4.0)

        res = GraphAlgorithms.prim_mst(g, start_vertex="A")

        self.assertEqual(res["edge_count"], 3)
        self.assertEqual(res["total_weight"], 7.0)  # (A-C:1), (C-B:2), (C-D:4) -> 7.0

    def test_13_dijkstra_shortest_path(self):
        """Test 13: Dijkstra's algorithm for single-source shortest path."""
        g = Graph(directed=False)
        g.add_edge("S", "A", 4.0)
        g.add_edge("S", "B", 2.0)
        g.add_edge("B", "A", 1.0)
        g.add_edge("A", "T", 3.0)
        g.add_edge("B", "T", 6.0)

        # Shortest S -> T is S -> B (2) -> A (1) -> T (3) = 6.0
        res = GraphAlgorithms.dijkstra_shortest_path(g, source="S", target="T")

        self.assertEqual(res["target_distance"], 6.0)
        self.assertEqual(res["shortest_path"], ["S", "B", "A", "T"])

    def test_14_bellman_ford_negative_cycle(self):
        """Test 14: Bellman-Ford negative-cycle detection."""
        # 1. Graph without negative cycle
        g_valid = Graph(directed=True)
        g_valid.add_edge("0", "1", 4.0)
        g_valid.add_edge("0", "2", 5.0)
        g_valid.add_edge("1", "2", -2.0)  # Negative edge, no cycle

        res_valid = GraphAlgorithms.bellman_ford(g_valid, source="0")
        self.assertFalse(res_valid["has_negative_cycle"])
        self.assertEqual(res_valid["distances"]["2"], 2.0)

        # 2. Graph with negative cycle (A -> B (1) -> C (-4) -> A (1) = -2)
        g_cycle = Graph(directed=True)
        g_cycle.add_edge("A", "B", 1.0)
        g_cycle.add_edge("B", "C", -4.0)
        g_cycle.add_edge("C", "A", 1.0)

        res_cycle = GraphAlgorithms.bellman_ford(g_cycle, source="A")
        self.assertTrue(res_cycle["has_negative_cycle"])

    def test_15_floyd_warshall_all_pairs(self):
        """Test 15: Floyd-Warshall all-pairs shortest paths."""
        g = Graph(directed=True)
        g.add_edge("1", "2", 3.0)
        g.add_edge("2", "3", 1.0)
        g.add_edge("1", "3", 8.0)

        res = GraphAlgorithms.floyd_warshall(g)
        v = res["vertices"]  # ['1', '2', '3']
        idx = {node: i for i, node in enumerate(v)}

        dist_1_to_3 = res["distance_matrix"][idx["1"]][idx["3"]]
        self.assertEqual(dist_1_to_3, 4.0)  # 1 -> 2 (3) + 2 -> 3 (1) = 4.0

    def test_transitive_closure_warshall(self):
        """Test Warshall's Transitive Closure reachability matrix."""
        g = Graph(directed=True)
        g.add_edge("A", "B", 1.0)
        g.add_edge("B", "C", 1.0)
        # No edge back to A, no edge from C

        res = GraphAlgorithms.transitive_closure_warshall(g)
        v = res["vertices"]
        idx = {node: i for i, node in enumerate(v)}

        matrix = res["matrix"]
        self.assertEqual(matrix[idx["A"]][idx["C"]], 1)  # A can reach C
        self.assertEqual(matrix[idx["C"]][idx["A"]], 0)  # C cannot reach A


if __name__ == "__main__":
    unittest.main()
