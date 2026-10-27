"""
Graph Data Structure using Adjacency List representation.
DSA-II Project Requirement: Graph Representation for Duplicate Clusters & Algorithm Lab.
"""

from typing import Dict, List, Tuple, Any, Optional, Set


class Graph:
    """
    General-purpose Graph class using an Adjacency List.
    Supports both directed and undirected graphs, weighted edges, and node metadata.
    """

    def __init__(self, directed: bool = False):
        self.directed: bool = directed
        # Adjacency list: vertex_id -> list of (neighbor_id, weight)
        self.adj: Dict[str, List[Tuple[str, float]]] = {}
        # Vertex metadata: vertex_id -> dict of attributes
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def add_vertex(self, vertex_id: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a vertex with optional metadata."""
        v = str(vertex_id)
        if v not in self.adj:
            self.adj[v] = []
            self.nodes[v] = data or {}
        elif data:
            self.nodes[v].update(data)

    def add_edge(
        self,
        u: str,
        v: str,
        weight: float = 1.0,
        bidirectional: Optional[bool] = None,
    ) -> None:
        """Add an edge between u and v with a weight."""
        u_str, v_str = str(u), str(v)
        self.add_vertex(u_str)
        self.add_vertex(v_str)

        # Add u -> v if not already present
        if not any(neighbor == v_str for neighbor, _ in self.adj[u_str]):
            self.adj[u_str].append((v_str, float(weight)))

        # Handle bidirectional (undirected)
        is_bi = (not self.directed) if bidirectional is None else bidirectional
        if is_bi:
            if not any(neighbor == u_str for neighbor, _ in self.adj[v_str]):
                self.adj[v_str].append((u_str, float(weight)))

    def get_neighbors(self, vertex_id: str) -> List[Tuple[str, float]]:
        """Return list of (neighbor_id, weight) tuples for vertex_id."""
        return self.adj.get(str(vertex_id), [])

    def get_vertices(self) -> List[str]:
        """Return list of all vertex IDs."""
        return list(self.adj.keys())

    def get_vertex_data(self, vertex_id: str) -> Dict[str, Any]:
        """Get attributes dictionary for a vertex."""
        return self.nodes.get(str(vertex_id), {})

    def get_edges(self) -> List[Tuple[str, str, float]]:
        """
        Return list of all edges as (u, v, weight).
        For undirected graphs, each edge is returned once where u <= v.
        """
        edges = []
        seen = set()
        for u in self.adj:
            for v, w in self.adj[u]:
                if not self.directed:
                    edge_key = tuple(sorted([u, v]))
                    if edge_key not in seen:
                        seen.add(edge_key)
                        edges.append((u, v, w))
                else:
                    edges.append((u, v, w))
        return edges

    def vertex_count(self) -> int:
        """Return total number of vertices |V|."""
        return len(self.adj)

    def edge_count(self) -> int:
        """Return total number of edges |E|."""
        return len(self.get_edges())

    def clear(self) -> None:
        """Clear all vertices and edges."""
        self.adj.clear()
        self.nodes.clear()

    @classmethod
    def build_from_duplicate_groups(cls, duplicate_groups: List[Dict[str, Any]]) -> "Graph":
        """
        Construct an undirected duplicate graph from verified duplicate groups.
        
        Vertices: File copies
        Edges: Full mesh (clique) among all files with identical content in each group.
        Weight: File size or 1.0 (unweighted equivalence).
        """
        g = cls(directed=False)

        for group in duplicate_groups:
            group_id = group.get("group_id", group.get("group_hash", ""))
            files = group.get("files", [])
            file_size = group.get("file_size", 0)

            # Add all vertices
            for f in files:
                fid = str(f["file_id"])
                g.add_vertex(
                    fid,
                    data={
                        "filename": f["filename"],
                        "path": f["path"],
                        "size": file_size,
                        "group_id": group_id,
                        "is_canonical": f.get("is_canonical", False),
                    },
                )

            # Connect all pairs within group (complete subgraph / equivalence clique)
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    u = str(files[i]["file_id"])
                    v = str(files[j]["file_id"])
                    g.add_edge(u, v, weight=1.0)

        return g

    @classmethod
    def build_sample_weighted_graph(cls) -> "Graph":
        """
        Construct an illustrative weighted graph for algorithm demonstrations
        (Kruskal, Prim, Dijkstra, Bellman-Ford, Floyd-Warshall).
        
        Nodes represent file nodes / backup nodes, weights represent link latency / cost.
        """
        g = cls(directed=False)
        nodes = ["FileA", "FileB", "FileC", "FileD", "FileE", "FileF"]
        for n in nodes:
            g.add_vertex(n, data={"label": n})

        # Weighted edges
        weighted_edges = [
            ("FileA", "FileB", 4.0),
            ("FileA", "FileC", 2.0),
            ("FileB", "FileC", 1.0),
            ("FileB", "FileD", 5.0),
            ("FileC", "FileD", 8.0),
            ("FileC", "FileE", 10.0),
            ("FileD", "FileE", 2.0),
            ("FileD", "FileF", 6.0),
            ("FileE", "FileF", 3.0),
        ]

        for u, v, w in weighted_edges:
            g.add_edge(u, v, weight=w)

        return g
