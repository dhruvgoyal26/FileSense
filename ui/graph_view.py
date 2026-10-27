"""
Graph Analysis and Visualization Screen for FileSense.
Visualizes duplicate file clusters as an Undirected Graph using an Adjacency List.
Runs DFS and BFS to discover and analyze connected components.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
from app.config import format_bytes
from app.graph_structure import Graph
from app.graph_algorithms import GraphAlgorithms
from ui.styles import COLORS, FONTS


class GraphView(ttk.Frame):
    """
    Visual graph explorer representing verified duplicates as graph vertices and edges,
    with interactive DFS and BFS traversal demonstrations.
    """

    def __init__(
        self,
        parent: tk.Widget,
        get_duplicate_groups: Callable[[], List[Dict[str, Any]]],
    ):
        super().__init__(parent)
        self.get_duplicate_groups = get_duplicate_groups
        self.graph: Optional[Graph] = None
        self.node_positions: Dict[str, tuple[float, float]] = {}
        self.selected_node: Optional[str] = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Header Toolbar
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Duplicate Relationship Graph & Traversal Lab", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Undirected Adjacency-List Graph: Equivalence classes form disjoint connected components.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Action Buttons
        btn_box = ttk.Frame(header)
        btn_box.pack(side=tk.RIGHT)
        ttk.Button(btn_box, text="⚡ Run DFS", style="Primary.TButton", command=self._run_dfs).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="⚡ Run BFS", style="Success.TButton", command=self._run_bfs).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="🔄 Reload Graph", style="Secondary.TButton", command=self.load_graph_data).pack(side=tk.LEFT, padx=3)

        # Graph Canvas and Inspector Paned Window
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # LEFT: Interactive Canvas
        canvas_card = tk.Frame(paned, bg="#ffffff", highlightbackground=COLORS["border_light"], highlightthickness=1)
        paned.add(canvas_card, weight=3)

        self.canvas = tk.Canvas(canvas_card, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # RIGHT: Traversal Telemetry and Node Inspector
        inspector_frame = tk.Frame(paned, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=14, pady=12)
        paned.add(inspector_frame, weight=1)

        tk.Label(inspector_frame, text="Algorithm Telemetry", font=FONTS["title_medium"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")

        self.telemetry_text = tk.Text(
            inspector_frame,
            wrap="word",
            height=12,
            font=FONTS["mono"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8,
        )
        self.telemetry_text.pack(fill=tk.X, pady=(6, 12))

        tk.Label(inspector_frame, text="Selected Vertex Details", font=FONTS["title_medium"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")

        self.details_text = tk.Text(
            inspector_frame,
            wrap="word",
            height=10,
            font=FONTS["mono"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8,
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.telemetry_text.insert("1.0", "Select DFS or BFS to traverse the duplicate relationship graph.")
        self.details_text.insert("1.0", "Click on any node in the graph canvas to inspect its file metadata.")

    def load_graph_data(self) -> None:
        """Construct graph from discovered duplicate groups."""
        groups = self.get_duplicate_groups()
        if not groups:
            self.graph = None
            self._render_empty_state("No duplicate files detected yet.\nRun 'Find Duplicates' to construct the relationship graph.")
            return

        self.graph = Graph.build_from_duplicate_groups(groups)
        self._layout_and_render_graph()

    def _render_empty_state(self, msg: str) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 600
        h = self.canvas.winfo_height() or 400
        self.canvas.create_text(
            w / 2,
            h / 2,
            text=msg,
            font=FONTS["title_medium"],
            fill=COLORS["text_muted"],
            justify="center",
        )

    def _layout_and_render_graph(self, highlighted_edges: Optional[List[tuple]] = None, traversal_order: Optional[List[str]] = None) -> None:
        """Lay out clusters in circular orbits and render edges and nodes."""
        if not self.graph or self.graph.vertex_count() == 0:
            self._render_empty_state("Duplicate graph is empty.")
            return

        self.canvas.delete("all")
        w = max(400, self.canvas.winfo_width())
        h = max(300, self.canvas.winfo_height())

        # Partition vertices by duplicate group ID
        groups_dict: Dict[Any, List[str]] = {}
        for v in self.graph.get_vertices():
            v_data = self.graph.get_vertex_data(v)
            gid = v_data.get("group_id", "default")
            if gid not in groups_dict:
                groups_dict[gid] = []
            groups_dict[gid].append(v)

        num_groups = len(groups_dict)
        group_centers: Dict[Any, tuple[float, float]] = {}

        # Center coordinates for each group
        if num_groups == 1:
            group_centers[list(groups_dict.keys())[0]] = (w / 2, h / 2)
        else:
            outer_radius = min(w, h) * 0.32
            for idx, gid in enumerate(groups_dict.keys()):
                angle = (2 * math.pi * idx) / num_groups
                cx = w / 2 + outer_radius * math.cos(angle)
                cy = h / 2 + outer_radius * math.sin(angle)
                group_centers[gid] = (cx, cy)

        # Place nodes within group cluster
        self.node_positions.clear()
        group_colors = ["#2563eb", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4", "#f97316", "#64748b"]

        for g_idx, (gid, members) in enumerate(groups_dict.items()):
            cx, cy = group_centers[gid]
            color = group_colors[g_idx % len(group_colors)]
            k = len(members)

            # Draw cluster background aura
            cluster_r = 50 + k * 12
            self.canvas.create_oval(
                cx - cluster_r, cy - cluster_r, cx + cluster_r, cy + cluster_r,
                fill="#f8fafc", outline="#e2e8f0", width=1, dash=(4, 4)
            )
            self.canvas.create_text(
                cx, cy - cluster_r + 12,
                text=f"Group #{gid} ({k} copies)",
                font=FONTS["caption"],
                fill=COLORS["text_muted"]
            )

            if k == 1:
                self.node_positions[members[0]] = (cx, cy)
            else:
                sub_r = min(cluster_r * 0.65, 40 + k * 8)
                for m_idx, v in enumerate(members):
                    sub_angle = (2 * math.pi * m_idx) / k
                    nx = cx + sub_r * math.cos(sub_angle)
                    ny = cy + sub_r * math.sin(sub_angle)
                    self.node_positions[v] = (nx, ny)

        # Draw Edges
        edges = self.graph.get_edges()
        for u, v, _ in edges:
            if u in self.node_positions and v in self.node_positions:
                x1, y1 = self.node_positions[u]
                x2, y2 = self.node_positions[v]
                self.canvas.create_line(x1, y1, x2, y2, fill="#94a3b8", width=2)

        # Draw Nodes
        node_radius = 16
        for v, (x, y) in self.node_positions.items():
            v_data = self.graph.get_vertex_data(v)
            is_canonical = v_data.get("is_canonical", False)

            # Border/fill
            node_color = "#10b981" if is_canonical else "#3b82f6"
            border_color = "#047857" if is_canonical else "#1d4ed8"
            border_width = 3 if is_canonical else 2

            # Traversal order index tag
            order_idx = None
            if traversal_order and v in traversal_order:
                order_idx = traversal_order.index(v) + 1

            self.canvas.create_oval(
                x - node_radius, y - node_radius, x + node_radius, y + node_radius,
                fill=node_color, outline=border_color, width=border_width,
                tags=("node", f"node_{v}")
            )

            # Label text inside node or order index
            label_text = str(order_idx) if order_idx else v
            self.canvas.create_text(
                x, y,
                text=label_text,
                fill="#ffffff",
                font=FONTS["body_bold"],
                tags=("node", f"node_{v}")
            )

            # Filename below node
            fn = v_data.get("filename", "")
            if len(fn) > 16:
                fn = fn[:13] + "..."
            self.canvas.create_text(
                x, y + node_radius + 10,
                text=fn,
                font=FONTS["caption"],
                fill=COLORS["text_primary"],
            )

    def _on_canvas_click(self, event) -> None:
        """Handle clicking node on canvas to inspect metadata."""
        if not self.graph:
            return

        cx, cy = event.x, event.y
        clicked_node = None

        for v, (nx, ny) in self.node_positions.items():
            dist = math.hypot(cx - nx, cy - ny)
            if dist <= 20:
                clicked_node = v
                break

        if clicked_node:
            self.selected_node = clicked_node
            v_data = self.graph.get_vertex_data(clicked_node)
            self.details_text.configure(state="normal")
            self.details_text.delete("1.0", tk.END)

            details = (
                f"Vertex ID: {clicked_node}\n"
                f"Role: {'CANONICAL MASTER' if v_data.get('is_canonical') else 'Redundant Copy'}\n"
                f"Filename: {v_data.get('filename')}\n"
                f"Size: {format_bytes(v_data.get('size', 0))}\n"
                f"Group ID: {v_data.get('group_id')}\n"
                f"Path: {v_data.get('path')}\n\n"
                f"Adjacency Degree: {len(self.graph.get_neighbors(clicked_node))}\n"
                f"Identical Neighbors:\n"
            )
            for n_id, _ in self.graph.get_neighbors(clicked_node):
                n_data = self.graph.get_vertex_data(n_id)
                details += f"  ➜ [{n_id}] {n_data.get('filename')}\n"

            self.details_text.insert("1.0", details)
            self.details_text.configure(state="disabled")

    def _run_dfs(self) -> None:
        """Run Depth-First Search on the duplicate graph."""
        if not self.graph:
            self.load_graph_data()
        if not self.graph or self.graph.vertex_count() == 0:
            messagebox.showinfo("Graph Empty", "No duplicate graph to traverse.")
            return

        start_v = self.selected_node or (self.graph.get_vertices()[0] if self.graph.get_vertices() else None)
        result = GraphAlgorithms.dfs_traversal(self.graph, start_vertex=start_v)

        self._render_traversal_results(result)
        self._layout_and_render_graph(traversal_order=result["traversal_order"])

    def _run_bfs(self) -> None:
        """Run Breadth-First Search on the duplicate graph."""
        if not self.graph:
            self.load_graph_data()
        if not self.graph or self.graph.vertex_count() == 0:
            messagebox.showinfo("Graph Empty", "No duplicate graph to traverse.")
            return

        start_v = self.selected_node or (self.graph.get_vertices()[0] if self.graph.get_vertices() else None)
        result = GraphAlgorithms.bfs_traversal(self.graph, start_vertex=start_v)

        self._render_traversal_results(result)
        self._layout_and_render_graph(traversal_order=result["traversal_order"])

    def _render_traversal_results(self, res: Dict[str, Any]) -> None:
        """Format and print traversal telemetry."""
        self.telemetry_text.configure(state="normal")
        self.telemetry_text.delete("1.0", tk.END)

        order_str = " ➜ ".join(res["traversal_order"])
        telemetry = (
            f"Algorithm: {res['algorithm']}\n"
            f"Input Vertices |V|: {res['vertex_count']}\n"
            f"Input Edges |E|: {res['edge_count']}\n"
            f"Connected Components: {res['component_count']}\n"
            f"Execution Time: {res['execution_time_ms']:.3f} ms\n\n"
            f"Traversal Sequence:\n{order_str}\n\n"
            f"Discovered Component Clusters:\n"
        )
        for idx, comp in enumerate(res["components"], 1):
            telemetry += f"  Cluster {idx} ({len(comp)} nodes): {', '.join(comp)}\n"

        self.telemetry_text.insert("1.0", telemetry)
        self.telemetry_text.configure(state="disabled")
