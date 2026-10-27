"""
Algorithm Lab Screen for FileSense.
DSA-II Academic Demonstration Hub:
- Graph Traversal: DFS & BFS
- Minimum Spanning Trees: Kruskal (DSU) & Prim (Priority Queue)
- Shortest Paths: Dijkstra, Bellman-Ford, Floyd-Warshall
- Transitive Closure: Warshall Reachability Matrix
- Dynamic Programming: 0/1 Knapsack, Resource Allocation, LCS, MCM
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any
from app.graph_structure import Graph
from app.graph_algorithms import GraphAlgorithms
from app.dynamic_programming import (
    solve_knapsack_01,
    solve_resource_allocation,
    solve_lcs,
    solve_matrix_chain_multiplication,
)
from ui.styles import COLORS, FONTS


class AlgorithmLabView(ttk.Frame):
    """
    Algorithm Lab for testing and demonstrating DSA-II core algorithms.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        # Header Toolbar
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="DSA-II Algorithm Demonstration Lab", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Interactive execution of graph algorithms, transitive closure, and dynamic programming.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Tabbed Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Tab 1: Graph Traversal (DFS & BFS)
        tab_traversal = ttk.Frame(notebook)
        notebook.add(tab_traversal, text="1. Traversal (DFS/BFS)")
        self._build_traversal_tab(tab_traversal)

        # Tab 2: Minimum Spanning Trees (Kruskal & Prim)
        tab_mst = ttk.Frame(notebook)
        notebook.add(tab_mst, text="2. Spanning Trees (Kruskal/Prim)")
        self._build_mst_tab(tab_mst)

        # Tab 3: Shortest Paths (Dijkstra, Bellman-Ford, Floyd-Warshall)
        tab_sp = ttk.Frame(notebook)
        notebook.add(tab_sp, text="3. Shortest Paths (Dijkstra/Bellman/Floyd)")
        self._build_shortest_paths_tab(tab_sp)

        # Tab 4: Transitive Closure (Warshall)
        tab_tc = ttk.Frame(notebook)
        notebook.add(tab_tc, text="4. Transitive Closure (Warshall)")
        self._build_transitive_closure_tab(tab_tc)

        # Tab 5: Dynamic Programming (Knapsack, Resource Allocation, LCS, MCM)
        tab_dp = ttk.Frame(notebook)
        notebook.add(tab_dp, text="5. Dynamic Programming (DP)")
        self._build_dp_tab(tab_dp)

    # ==========================================================
    # Tab 1: DFS & BFS
    # ==========================================================
    def _build_traversal_tab(self, parent: ttk.Frame) -> None:
        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_bar = tk.Frame(card, bg=COLORS["bg_card"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_bar, text="Target Graph: Connected Components Benchmark Graph", font=FONTS["body_bold"], bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Run DFS (Depth-First)", style="Primary.TButton", command=self._run_lab_dfs).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_bar, text="Run BFS (Breadth-First)", style="Success.TButton", command=self._run_lab_bfs).pack(side=tk.RIGHT, padx=4)

        self.txt_traversal = tk.Text(card, wrap="word", font=FONTS["mono"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        self.txt_traversal.pack(fill=tk.BOTH, expand=True)

        self.txt_traversal.insert(
            "1.0",
            "Click 'Run DFS' or 'Run BFS' to execute graph traversal.\n\n"
            "Academic Context:\n"
            "DFS explores branch depths using recursion/stack (Time: O(V + E), Space: O(V)).\n"
            "BFS explores levels sequentially using a FIFO queue (Time: O(V + E), Space: O(V)).\n"
            "Both algorithms discover all connected components in an undirected duplicate graph.",
        )

    def _run_lab_dfs(self) -> None:
        g = Graph.build_sample_weighted_graph()
        res = GraphAlgorithms.dfs_traversal(g, start_vertex="FileA")
        out = (
            f"=== {res['algorithm']} Execution Results ===\n"
            f"Input Graph Vertices |V|: {res['vertex_count']}\n"
            f"Input Graph Edges |E|: {res['edge_count']}\n"
            f"Connected Components: {res['component_count']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n\n"
            f"Traversal Order: {' ➜ '.join(res['traversal_order'])}\n\n"
            f"Discovered Component Sets:\n"
        )
        for i, comp in enumerate(res["components"], 1):
            out += f"  Component {i}: {comp}\n"
        out += "\nTime Complexity: O(V + E)\nAuxiliary Space: O(V)"

        self.txt_traversal.delete("1.0", tk.END)
        self.txt_traversal.insert("1.0", out)

    def _run_lab_bfs(self) -> None:
        g = Graph.build_sample_weighted_graph()
        res = GraphAlgorithms.bfs_traversal(g, start_vertex="FileA")
        out = (
            f"=== {res['algorithm']} Execution Results ===\n"
            f"Input Graph Vertices |V|: {res['vertex_count']}\n"
            f"Input Graph Edges |E|: {res['edge_count']}\n"
            f"Connected Components: {res['component_count']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n\n"
            f"Traversal Order: {' ➜ '.join(res['traversal_order'])}\n\n"
            f"BFS Level Distances from 'FileA':\n"
        )
        for node, lvl in sorted(res["levels"].items()):
            out += f"  • {node}: Level {lvl}\n"
        out += "\nTime Complexity: O(V + E)\nAuxiliary Space: O(V)"

        self.txt_traversal.delete("1.0", tk.END)
        self.txt_traversal.insert("1.0", out)

    # ==========================================================
    # Tab 2: Kruskal & Prim MST
    # ==========================================================
    def _build_mst_tab(self, parent: ttk.Frame) -> None:
        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_bar = tk.Frame(card, bg=COLORS["bg_card"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_bar, text="Minimum Spanning Tree on Weighted File Relationship Network", font=FONTS["body_bold"], bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Run Kruskal (DSU)", style="Primary.TButton", command=self._run_lab_kruskal).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_bar, text="Run Prim (Priority Queue)", style="Success.TButton", command=self._run_lab_prim).pack(side=tk.RIGHT, padx=4)

        self.txt_mst = tk.Text(card, wrap="word", font=FONTS["mono"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        self.txt_mst.pack(fill=tk.BOTH, expand=True)

        self.txt_mst.insert(
            "1.0",
            "Minimum Spanning Tree (MST) Algorithms:\n\n"
            "IMPORTANT ACADEMIC NOTE (DSA-II):\n"
            "A duplicate graph's verified-equality edges do not represent costs or network links.\n"
            "Spanning trees do not determine file deletions. For this demonstration, we use\n"
            "an illustrative weighted file relationship graph where weights represent transfer latency / sync cost.\n\n"
            "• Kruskal's Algorithm: Sorts edges by weight and uses Disjoint Set Union (Union-Find) with path compression.\n"
            "• Prim's Algorithm: Grows a single tree from a start vertex using a Min-Heap priority queue.\n",
        )

    def _run_lab_kruskal(self) -> None:
        g = Graph.build_sample_weighted_graph()
        res = GraphAlgorithms.kruskal_mst(g)
        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Input Vertices |V|: {res['vertex_count']}\n"
            f"Original Edges |E|: {res['original_edge_count']}\n"
            f"MST Tree Edges (|V|-1): {res['edge_count']}\n"
            f"Total MST Weight: {res['total_weight']:.2f}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"Selected Spanning Tree Edges (Sorted by weight):\n"
        )
        for u, v, w in res["mst_edges"]:
            out += f"  ({u} ── {v}) with weight {w}\n"

        self.txt_mst.delete("1.0", tk.END)
        self.txt_mst.insert("1.0", out)

    def _run_lab_prim(self) -> None:
        g = Graph.build_sample_weighted_graph()
        res = GraphAlgorithms.prim_mst(g, start_vertex="FileA")
        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Start Vertex: {res['start_vertex']}\n"
            f"Input Vertices |V|: {res['vertex_count']}\n"
            f"MST Tree Edges: {res['edge_count']}\n"
            f"Total MST Weight: {res['total_weight']:.2f}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"Selected Spanning Tree Edges (Priority Queue Expansion):\n"
        )
        for u, v, w in res["mst_edges"]:
            out += f"  ({u} ── {v}) with weight {w}\n"

        self.txt_mst.delete("1.0", tk.END)
        self.txt_mst.insert("1.0", out)

    # ==========================================================
    # Tab 3: Shortest Paths
    # ==========================================================
    def _build_shortest_paths_tab(self, parent: ttk.Frame) -> None:
        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_bar = tk.Frame(card, bg=COLORS["bg_card"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_bar, text="Shortest Paths on Weighted Graphs", font=FONTS["body_bold"], bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Dijkstra (FileA ➜ FileF)", style="Primary.TButton", command=self._run_lab_dijkstra).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_bar, text="Bellman-Ford", style="Success.TButton", command=self._run_lab_bellman).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_bar, text="Floyd-Warshall (All-Pairs)", style="Secondary.TButton", command=self._run_lab_floyd).pack(side=tk.RIGHT, padx=4)

        self.txt_sp = tk.Text(card, wrap="word", font=FONTS["mono"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        self.txt_sp.pack(fill=tk.BOTH, expand=True)

        self.txt_sp.insert(
            "1.0",
            "Shortest Path Algorithms in DSA-II:\n\n"
            "1. Dijkstra's Algorithm: Greedy single-source shortest path using Min-Heap priority queue.\n"
            "   Requires non-negative edge weights. Time: O((V + E) log V).\n\n"
            "2. Bellman-Ford Algorithm: Dynamic relaxation (|V|-1 passes) capable of handling negative edge weights\n"
            "   and detecting negative-weight cycles. Time: O(V * E).\n\n"
            "3. Floyd-Warshall Algorithm: All-pairs shortest path dynamic programming computing full distance matrix.\n"
            "   Time: O(V^3), Space: O(V^2).\n",
        )

    def _run_lab_dijkstra(self) -> None:
        g = Graph.build_sample_weighted_graph()
        res = GraphAlgorithms.dijkstra_shortest_path(g, source="FileA", target="FileF")
        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Source: {res['source']} ➜ Destination: {res['target']}\n"
            f"Shortest Path: {' ➜ '.join(res['shortest_path'])}\n"
            f"Total Path Distance: {res['target_distance']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"All Node Distances from '{res['source']}':\n"
        )
        for node, d in sorted(res["all_distances"].items()):
            out += f"  • {node}: distance = {d}\n"

        self.txt_sp.delete("1.0", tk.END)
        self.txt_sp.insert("1.0", out)

    def _run_lab_bellman(self) -> None:
        g = Graph(directed=True)
        g.add_edge("FileA", "FileB", 4.0)
        g.add_edge("FileA", "FileC", 5.0)
        g.add_edge("FileB", "FileC", -2.0)  # Negative weight edge
        g.add_edge("FileC", "FileD", 3.0)

        res = GraphAlgorithms.bellman_ford(g, source="FileA")
        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Source Vertex: {res['source']}\n"
            f"Negative Cycle Detected: {'YES (Cycle Found!)' if res['has_negative_cycle'] else 'NO (Safe)'}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"Computed Shortest Distances (Accommodating Negative Edge B ➜ C = -2.0):\n"
        )
        for node, d in sorted(res["distances"].items()):
            out += f"  • {node}: distance = {d}\n"

        self.txt_sp.delete("1.0", tk.END)
        self.txt_sp.insert("1.0", out)

    def _run_lab_floyd(self) -> None:
        g = Graph(directed=True)
        g.add_edge("A", "B", 3.0)
        g.add_edge("B", "C", 1.0)
        g.add_edge("A", "C", 8.0)
        g.add_edge("C", "D", 2.0)
        g.add_edge("B", "D", 7.0)

        res = GraphAlgorithms.floyd_warshall(g)
        v = res["vertices"]
        mat = res["distance_matrix"]

        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Vertex Count |V|: {res['vertex_count']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"All-Pairs Shortest Path Distance Matrix D:\n\n"
            f"       " + "  ".join(f"{node:>6}" for node in v) + "\n"
        )
        for i, row_node in enumerate(v):
            row_str = f"{row_node:>4} : "
            for j in range(len(v)):
                val = mat[i][j]
                val_str = "inf" if val == float("inf") else f"{val:.1f}"
                row_str += f"{val_str:>6}  "
            out += row_str + "\n"

        self.txt_sp.delete("1.0", tk.END)
        self.txt_sp.insert("1.0", out)

    # ==========================================================
    # Tab 4: Transitive Closure (Warshall)
    # ==========================================================
    def _build_transitive_closure_tab(self, parent: ttk.Frame) -> None:
        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_bar = tk.Frame(card, bg=COLORS["bg_card"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_bar, text="Warshall's Algorithm for Reachability Matrix", font=FONTS["body_bold"], bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Compute Reachability Matrix", style="Primary.TButton", command=self._run_lab_warshall).pack(side=tk.RIGHT)

        self.txt_tc = tk.Text(card, wrap="word", font=FONTS["mono"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        self.txt_tc.pack(fill=tk.BOTH, expand=True)

        self.txt_tc.insert(
            "1.0",
            "Warshall's Algorithm for Transitive Closure:\n\n"
            "Given a directed graph G = (V, E), the transitive closure is a boolean reachability matrix R\n"
            "where R[i][j] = 1 if there exists a directed path from vertex i to vertex j, else 0.\n\n"
            "Dynamic Programming Recurrence:\n"
            "  R^(k)[i][j] = R^(k-1)[i][j] OR (R^(k-1)[i][k] AND R^(k-1)[k][j])\n\n"
            "Time Complexity: O(V^3)\n"
            "Space Complexity: O(V^2)\n"
            "Note: Designed for small-to-moderate graphs. Click 'Compute Reachability Matrix' to run.",
        )

    def _run_lab_warshall(self) -> None:
        g = Graph(directed=True)
        nodes = ["Node1", "Node2", "Node3", "Node4"]
        for n in nodes:
            g.add_vertex(n)
        # 1 -> 2, 2 -> 3, 3 -> 4
        g.add_edge("Node1", "Node2")
        g.add_edge("Node2", "Node3")
        g.add_edge("Node3", "Node4")

        res = GraphAlgorithms.transitive_closure_warshall(g)
        v = res["vertices"]
        mat = res["matrix"]

        out = (
            f"=== {res['algorithm']} Results ===\n"
            f"Vertex Count |V|: {res['vertex_count']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"Reachability Matrix R (1 = Path exists, 0 = Unreachable):\n\n"
            f"         " + "  ".join(f"{node:>7}" for node in v) + "\n"
        )
        for i, row_node in enumerate(v):
            row_str = f"{row_node:>7} : "
            for j in range(len(v)):
                row_str += f"{mat[i][j]:>7}  "
            out += row_str + "\n"

        out += "\nInterpretation:\nNode1 has paths to Node2, Node3, and Node4. Node4 has no outgoing paths."

        self.txt_tc.delete("1.0", tk.END)
        self.txt_tc.insert("1.0", out)

    # ==========================================================
    # Tab 5: Dynamic Programming (DP)
    # ==========================================================
    def _build_dp_tab(self, parent: ttk.Frame) -> None:
        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_bar = tk.Frame(card, bg=COLORS["bg_card"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_bar, text="Dynamic Programming Suite", font=FONTS["body_bold"], bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="1. 0/1 Knapsack", style="Primary.TButton", command=self._run_lab_knapsack).pack(side=tk.LEFT, padx=(20, 4))
        ttk.Button(top_bar, text="2. Resource Allocation", style="Secondary.TButton", command=self._run_lab_resource_alloc).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_bar, text="3. LCS Text Similarity", style="Secondary.TButton", command=self._run_lab_lcs).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_bar, text="4. Matrix Chain (MCM)", style="Secondary.TButton", command=self._run_lab_mcm).pack(side=tk.LEFT, padx=4)

        self.txt_dp = tk.Text(card, wrap="word", font=FONTS["mono"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        self.txt_dp.pack(fill=tk.BOTH, expand=True)

        self.txt_dp.insert(
            "1.0",
            "DSA-II Dynamic Programming Requirements:\n\n"
            "Click any of the buttons above to execute and inspect the actual DP table and results:\n"
            "1. 0/1 Knapsack: Optimizes storage cleanup actions under a budget.\n"
            "2. Resource Allocation DP: Distributes cleanup budget across projects for maximum objective value.\n"
            "3. Longest Common Subsequence (LCS): Computes text similarity and shows the (m+1)x(n+1) DP grid.\n"
            "4. Matrix Chain Multiplication: Evaluates optimal parenthesization using split table s[i, j].\n",
        )

    def _run_lab_knapsack(self) -> None:
        items = [
            {"name": "Backup_Archive.zip", "size": 150, "utility": 80},
            {"name": "Old_Dataset.csv", "size": 200, "utility": 120},
            {"name": "Temp_Render.mp4", "size": 300, "utility": 200},
            {"name": "Raw_Logs.txt", "size": 100, "utility": 50},
        ]
        budget = 400

        res = solve_knapsack_01(items, budget)
        out = (
            f"=== 0/1 Knapsack Storage Cleanup DP ===\n"
            f"Target Storage Budget: {res['budget']} MB\n"
            f"Candidate Items: {res['item_count']}\n"
            f"Optimal Value / Utility Achieved: {res['optimal_value']}\n"
            f"Total Storage Selected: {res['total_selected_size']} MB\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n\n"
            f"Selected Items via DP Traceback:\n"
        )
        for it in res["selected_items"]:
            out += f"  • {it['name']} (Size: {it['size']} MB, Utility: {it['utility']})\n"

        out += "\nSample DP Table slice (Items x Scaled Budget):\n"
        for r_idx, row in enumerate(res["dp_table_sample"]):
            out += f"  Row {r_idx}: {row}\n"

        self.txt_dp.delete("1.0", tk.END)
        self.txt_dp.insert("1.0", out)

    def _run_lab_resource_alloc(self) -> None:
        activities = ["Disk_A_Cleanup", "Disk_B_Cleanup", "Server_Sync"]
        utilities = [
            [0, 10, 18, 25],
            [0, 12, 20, 24],
            [0, 8, 15, 21],
        ]
        budget = 3

        res = solve_resource_allocation(activities, utilities, budget)
        out = (
            f"=== Resource Allocation DP ===\n"
            f"Total Resource Units to Distribute: {res['total_budget']}\n"
            f"Maximum Total Objective Value: {res['maximum_utility']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n\n"
            f"Optimal Allocation per Activity:\n"
        )
        for act, alloc in res["allocations"].items():
            out += f"  • {act}: {alloc} units\n"

        self.txt_dp.delete("1.0", tk.END)
        self.txt_dp.insert("1.0", out)

    def _run_lab_lcs(self) -> None:
        s1 = "FILESENSE_DSA"
        s2 = "FILE_REDUNDANCY_DSA"

        res = solve_lcs(s1, s2)
        out = (
            f"=== Longest Common Subsequence (LCS) DP ===\n"
            f"String 1: '{s1}' (Length {res['len1']})\n"
            f"String 2: '{s2}' (Length {res['len2']})\n"
            f"LCS Length: {res['lcs_length']}\n"
            f"LCS String Result: '{res['lcs_string']}'\n"
            f"Similarity Ratio: {res['similarity_ratio']:.2%}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"DP Matrix Table (m+1) x (n+1):\n"
        )
        # Print compact table
        grid = res["dp_table"]
        out += "       " + " ".join(f"{ch:>2}" for ch in (" " + s2)) + "\n"
        for i, row in enumerate(grid):
            label = " " if i == 0 else s1[i - 1]
            out += f"  {label:>2} : " + " ".join(f"{val:>2}" for val in row) + "\n"

        self.txt_dp.delete("1.0", tk.END)
        self.txt_dp.insert("1.0", out)

    def _run_lab_mcm(self) -> None:
        dimensions = [10, 20, 30, 40, 30]

        res = solve_matrix_chain_multiplication(dimensions)
        out = (
            f"=== Matrix Chain Multiplication (MCM) DP ===\n"
            f"Matrix Dimensions: {res['dimensions']}\n"
            f"Number of Matrices: {res['matrix_count']}\n"
            f"Minimum Scalar Multiplications: {res['minimum_multiplications']:,}\n"
            f"Optimal Parenthesization: {res['optimal_parenthesization']}\n"
            f"Execution Time: {res['execution_time_ms']:.4f} ms\n"
            f"Complexity: {res['complexity']}\n\n"
            f"Cost Table m[i, j]:\n"
        )
        m = res["cost_table"]
        n = res["matrix_count"]
        for i in range(1, n + 1):
            out += f"  Row {i}: " + "  ".join(f"{int(m[i][j]):>8}" for j in range(1, n + 1)) + "\n"

        self.txt_dp.delete("1.0", tk.END)
        self.txt_dp.insert("1.0", out)
