# FileSense — Algorithms & Complexity Reference
**Course**: Data Structures and Algorithms-II (CCSE0301)  
**Project**: High-Performance Local File Indexing and Redundancy Detection Tool  
**SDG Alignment**: SDG 9: Industry, Innovation and Infrastructure  

This document provides a rigorous mathematical and algorithmic analysis of all data structures, traversal algorithms, graph algorithms, and dynamic programming techniques implemented in **FileSense**.

---

## 1. HIERARCHICAL TREE DATA STRUCTURE

### Definition & Model
The filesystem hierarchy is represented in-memory as an N-ary Tree using the `TreeNode` and `DirectoryTree` structures:
- **Node definition**: Each node represents either a directory or a file, storing metadata (name, path, size, modification timestamp, category, content hash).
- **Pointers**: Explicit `parent` pointer and a dictionary of `children` indexed by directory/file name.
- **Subtree size caching**: Subtree sizes are lazily computed and invalidated upwards along the ancestor chain upon node modification.

### Traversals & Complexities
1. **Preorder Traversal ($Parent \to Children$)**:
   - Yields the parent node before recursively visiting each child sorted alphabetically.
   - Used for top-down folder indexing, path creation, and UI directory tree construction.
   - **Time Complexity**: $\mathcal{O}(N)$ where $N$ is total filesystem nodes.
   - **Space Complexity**: $\mathcal{O}(H)$ auxiliary call-stack space, where $H$ is directory tree depth ($\mathcal{O}(\log N)$ balanced, $\mathcal{O}(N)$ worst-case).

2. **Postorder Traversal ($Children \to Parent$)**:
   - Traverses all descendants before yielding the parent.
   - Used for bottom-up size aggregation and safe recursive subtree deletion.
   - **Time Complexity**: $\mathcal{O}(N)$.
   - **Space Complexity**: $\mathcal{O}(H)$.

---

## 2. HASH TABLE IN-MEMORY INDEXING

### In-Memory Hash Indexes
FileSense maintains multiple in-memory hash tables (Python dictionaries utilizing open-addressing with quadratic perturbation):
- `filename_index`: $\text{lower(filename)} \to [\text{file\_id}_1, \text{file\_id}_2, \dots]$
- `extension_index`: $\text{lower(ext)} \to [\text{file\_id}_1, \text{file\_id}_2, \dots]$
- `size_index`: $\text{size\_bytes} \to [\text{file\_id}_1, \text{file\_id}_2, \dots]$
- `content_hash_index`: $\text{sha256} \to [\text{file\_id}_1, \text{file\_id}_2, \dots]$
- `path_index`: $\text{normpath} \to \text{file\_id}$
- `records`: $\text{file\_id} \to \text{FileMetadataDict}$

### Mathematical Complexity
- **Insertion**: Average $\mathcal{O}(1)$, Worst-case $\mathcal{O}(N)$ under high collision clustering.
- **Exact Key Lookup**: Average $\mathcal{O}(1)$, Worst-case $\mathcal{O}(N)$.
- **Substring Filename Search**: $\mathcal{O}(K)$ where $K$ is total distinct filenames in index.
- **Compound Multi-Criteria Search**: Intersects candidate ID sets starting from the most selective hash table (e.g., extension or size index), reducing search space before linear predicate evaluation.

---

## 3. MULTI-STAGE DUPLICATE DETECTION PIPELINE

To avoid redundant disk I/O and prevent hashing non-duplicate files, FileSense implements a 3-stage filtration pipeline:

```
[All Indexed Files]
        │
        ▼ (Stage 1: Group by Size)
[Files with Identical Sizes] ──> Unique size files skipped (No I/O needed!)
        │
        ▼ (Stage 2: Chunked SHA-256 Streaming)
[Files with Identical Hashes] ──> Hash mismatches rejected
        │
        ▼ (Stage 3: Full Byte-for-Byte Verification)
[Confirmed Exact Duplicates] ──> Guaranteed zero cryptographic collision risk
```

### Storage Savings Formula
For a duplicate group containing $k$ identical files each of size $S$ bytes:
$$\text{Reclaimable Size} = (k - 1) \times S$$
$$\text{Total Storage Saved} = \sum_{g=1}^{G} (k_g - 1) \times S_g$$
FileSense guarantees **zero double counting** by partitioning discovered duplicates into disjoint equivalence groups.

---

## 4. GRAPH REPRESENTATION & TRAVERSALS

### Graph Model
- **Vertices ($V$)**: Indexed files participating in verified duplicate groups.
- **Edges ($E$)**: Equivalence relationships between files with verified identical content.
- **Representation**: Adjacency List `dict[str, list[tuple[str, float]]]`.
- **Equivalence Structure**: Because verified identity is reflexive, symmetric, and transitive, duplicate relationships naturally partition the graph into disjoint complete subgraphs (cliques $K_k$).

### A. Depth-First Search (DFS)
- **Purpose**: Discovers all connected components and determines equivalence group membership.
- **Mechanism**: Explores branches deeply using recursive or explicit stack traversal, tracking visited vertex sets.
- **Time Complexity**: $\mathcal{O}(V + E)$
- **Space Complexity**: $\mathcal{O}(V)$ auxiliary visited set and recursion stack.

### B. Breadth-First Search (BFS)
- **Purpose**: Level-order traversal from a start vertex using a FIFO queue.
- **Mechanism**: Visits all immediate neighbors at level $d$ before proceeding to level $d+1$.
- **Time Complexity**: $\mathcal{O}(V + E)$
- **Space Complexity**: $\mathcal{O}(V)$ queue and visited set.

---

## 5. DSA-II GRAPH ALGORITHMS (ALGORITHM LAB)

### C. Transitive Closure (Warshall's Algorithm)
- **Purpose**: Computes the reachability matrix $R$, where $R[i][j] = 1$ if there exists a directed path from vertex $i$ to vertex $j$.
- **Recurrence**:
  $$R^{(k)}[i][j] = R^{(k-1)}[i][j] \lor \left( R^{(k-1)}[i][k] \land R^{(k-1)}[k][j] \right)$$
- **Base Case**: $R^{(0)}[i][j] = 1$ if $(i, j) \in E$ or $i = j$, else $0$.
- **Time Complexity**: $\mathcal{O}(V^3)$ (3 nested loops over $|V|$ vertices).
- **Space Complexity**: $\mathcal{O}(V^2)$ for the boolean reachability matrix.
- **Intended Scope**: Small-to-moderate demonstration graphs.

### D. Kruskal's Minimum Spanning Tree (MST)
- **Purpose**: Finds the minimum spanning tree (or forest) on a weighted graph.
- **Mechanism**:
  1. Extract and sort all edges by weight: $w(e_1) \le w(e_2) \le \dots \le w(e_{|E|})$.
  2. Maintain a Disjoint Set Union (DSU / Union-Find) structure with **Path Compression** and **Union by Rank**.
  3. Iteratively add edge $(u, v)$ if $\text{Find}(u) \neq \text{Find}(v)$; reject if it creates a cycle.
- **Time Complexity**: $\mathcal{O}(E \log E) = \mathcal{O}(E \log V)$ for edge sorting; DSU operations run in near-constant $\mathcal{O}(\alpha(V))$ amortized time.
- **Space Complexity**: $\mathcal{O}(V)$ to maintain parent and rank tables in DSU.

### E. Prim's Minimum Spanning Tree (MST)
- **Purpose**: Grows a single spanning tree from an arbitrary root vertex.
- **Mechanism**:
  - Uses a Min-Heap priority queue storing candidate frontier edges $(w, u, v)$.
  - Greedily extracts the minimum-weight edge connecting an unvisited vertex.
- **Time Complexity**: $\mathcal{O}(E \log V)$ with binary heap.
- **Space Complexity**: $\mathcal{O}(V + E)$ for priority queue and visited tracking.

### F. Dijkstra's Shortest Path Algorithm
- **Purpose**: Single-source shortest path from source $s$ to all reachable vertices.
- **Constraint**: Edge weights must be non-negative ($w(e) \ge 0$).
- **Mechanism**:
  - Maintains `dist[v]` initialized to $\infty$, with `dist[s] = 0`.
  - Min-Heap extracts vertex $u$ with minimum distance; relaxes each outgoing edge $(u, v)$:
    $$\text{dist}[v] = \min(\text{dist}[v], \text{dist}[u] + w(u, v))$$
- **Time Complexity**: $\mathcal{O}((V + E) \log V)$ with binary min-heap.
- **Space Complexity**: $\mathcal{O}(V)$ for distance and predecessor maps.

### G. Bellman-Ford Shortest Path & Negative Cycle Detection
- **Purpose**: Single-source shortest paths on graphs with arbitrary (including negative) weights.
- **Mechanism**:
  - Relaxes all $|E|$ edges $|V| - 1$ times.
  - On the $|V|$-th iteration, if any distance can still be relaxed ($\text{dist}[u] + w < \text{dist}[v]$), a **negative-weight cycle** is detected.
- **Time Complexity**: $\mathcal{O}(V \times E)$.
- **Space Complexity**: $\mathcal{O}(V)$.

### H. Floyd-Warshall All-Pairs Shortest Path
- **Purpose**: Computes shortest path distances between every pair of vertices $(i, j)$.
- **Recurrence**:
  $$D^{(k)}[i][j] = \min\left( D^{(k-1)}[i][j],\; D^{(k-1)}[i][k] + D^{(k-1)}[k][j] \right)$$
- **Time Complexity**: $\mathcal{O}(V^3)$.
- **Space Complexity**: $\mathcal{O}(V^2)$ distance matrix.

---

## 6. DYNAMIC PROGRAMMING TECHNIQUES

### A. 0/1 Knapsack for Storage Cleanup Optimization
- **Problem Formulation**:
  Given a storage reclamation budget $W$ (maximum bytes to delete/reclaim) and $n$ independent candidate redundant cleanup files, each with size $w_i$ and priority utility score $v_i$, select a subset of files that maximizes total utility without exceeding budget $W$.
- **DP State**:
  $\text{dp}[i][w]$ = Maximum utility achievable considering items $1 \dots i$ under capacity limit $w$.
- **Recurrence**:
  $$\text{dp}[i][w] = \begin{cases}
  \text{dp}[i-1][w] & \text{if } w_i > w \\
  \max\left(\text{dp}[i-1][w],\; \text{dp}[i-1][w - w_i] + v_i\right) & \text{if } w_i \le w
  \end{cases}$$
- **Base Cases**: $\text{dp}[0][w] = 0$ for all $w$; $\text{dp}[i][0] = 0$ for all $i$.
- **Traceback**: Recovers exact chosen items by inspecting if $\text{dp}[i][w] \neq \text{dp}[i-1][w]$.
- **Time Complexity**: $\mathcal{O}(n \cdot W)$.
- **Space Complexity**: $\mathcal{O}(n \cdot W)$.

### B. Resource Allocation DP
- **Problem Formulation**:
  Distribute an integer budget $B$ among $N$ cleanup projects/categories to maximize total return:
  $$\text{dp}[i][b] = \max_{0 \le x \le b} \left( \text{dp}[i-1][b - x] + \text{utility}_i(x) \right)$$
- **Time Complexity**: $\mathcal{O}(N \cdot B^2)$.
- **Space Complexity**: $\mathcal{O}(N \cdot B)$.

### C. Longest Common Subsequence (LCS)
- **Problem Formulation**:
  Find the longest subsequence common to two text strings $X[0 \dots m-1]$ and $Y[0 \dots n-1]$.
- **Recurrence**:
  $$L[i][j] = \begin{cases}
  0 & \text{if } i=0 \text{ or } j=0 \\
  L[i-1][j-1] + 1 & \text{if } X[i-1] = Y[j-1] \\
  \max(L[i-1][j], L[i][j-1]) & \text{if } X[i-1] \neq Y[j-1]
  \end{cases}$$
- **Traceback**: Backtracks from $(m, n)$ to construct the actual common substring.
- **Time Complexity**: $\mathcal{O}(m \cdot n)$.
- **Space Complexity**: $\mathcal{O}(m \cdot n)$.

### D. Matrix Chain Multiplication (MCM)
- **Problem Formulation**:
  Given a sequence of matrices $\langle A_1, A_2, \dots, A_n \rangle$ where matrix $A_i$ has dimension $p_{i-1} \times p_i$, determine the parenthesization that minimizes scalar multiplications.
- **Recurrence**:
  $$m[i, j] = \begin{cases}
  0 & \text{if } i = j \\
  \min_{i \le k < j} \left( m[i, k] + m[k+1, j] + p_{i-1} p_k p_j \right) & \text{if } i < j
  \end{cases}$$
- **Traceback**: Uses split position table $s[i, j]$ to reconstruct parenthesization string (e.g. `((A1 × A2) × A3)`).
- **Time Complexity**: $\mathcal{O}(n^3)$.
- **Space Complexity**: $\mathcal{O}(n^2)$ for tables $m$ and $s$.

---

## 7. COMPLEXITY SUMMARY TABLE

| Algorithm / Structure | Time Complexity | Space Complexity | Real-world Project Application |
|---|---|---|---|
| **DirectoryTree (Preorder)** | $\mathcal{O}(N)$ | $\mathcal{O}(H)$ | Hierarchical filesystem indexing |
| **DirectoryTree (Postorder)** | $\mathcal{O}(N)$ | $\mathcal{O}(H)$ | Subtree size & metric rollup |
| **Hash Index Lookup** | $\mathcal{O}(1)$ avg | $\mathcal{O}(N)$ | Instant filename, ext, size search |
| **Stage 1 (Size Partitioning)** | $\mathcal{O}(N)$ | $\mathcal{O}(N)$ | Pre-screening candidate duplicates |
| **Stage 2 (Chunked SHA-256)** | $\mathcal{O}(B / \text{chunk})$ | $\mathcal{O}(1)$ RAM | Cryptographic content identification |
| **Stage 3 (Byte Verification)** | $\mathcal{O}(S / \text{chunk})$ | $\mathcal{O}(1)$ RAM | 100% collision-proof confirmation |
| **Duplicate Graph (Adj List)** | $\mathcal{O}(V + E)$ | $\mathcal{O}(V + E)$ | Duplicate relationship model |
| **DFS Traversal** | $\mathcal{O}(V + E)$ | $\mathcal{O}(V)$ | Connected components discovery |
| **BFS Traversal** | $\mathcal{O}(V + E)$ | $\mathcal{O}(V)$ | Level-by-level cluster traversal |
| **Transitive Closure (Warshall)**| $\mathcal{O}(V^3)$ | $\mathcal{O}(V^2)$ | Reachability matrix evaluation |
| **Kruskal's MST (DSU)** | $\mathcal{O}(E \log E)$ | $\mathcal{O}(V)$ | Spanning tree network optimization |
| **Prim's MST (Min-Heap)** | $\mathcal{O}(E \log V)$ | $\mathcal{O}(V + E)$ | Spanning tree frontier expansion |
| **Dijkstra's Shortest Path** | $\mathcal{O}((V + E) \log V)$ | $\mathcal{O}(V)$ | Latency path computation |
| **Bellman-Ford Algorithm** | $\mathcal{O}(V \cdot E)$ | $\mathcal{O}(V)$ | Negative cycle detection |
| **Floyd-Warshall Algorithm** | $\mathcal{O}(V^3)$ | $\mathcal{O}(V^2)$ | All-pairs distance matrix |
| **0/1 Knapsack DP** | $\mathcal{O}(n \cdot W)$ | $\mathcal{O}(n \cdot W)$ | Storage cleanup budget optimization |
| **Resource Allocation DP** | $\mathcal{O}(N \cdot B^2)$ | $\mathcal{O}(N \cdot B)$ | Distributing budget across targets |
| **Longest Common Subsequence** | $\mathcal{O}(m \cdot n)$ | $\mathcal{O}(m \cdot n)$ | Text similarity analysis |
| **Matrix Chain Multiplication** | $\mathcal{O}(n^3)$ | $\mathcal{O}(n^2)$ | Computational cost minimization |
