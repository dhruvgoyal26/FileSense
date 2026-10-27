# FileSense — PBL Evaluation & Demonstration Guide
**Course**: Data Structures and Algorithms-II (CCSE0301)  
**Project**: High-Performance Local File Indexing and Redundancy Detection Tool  
**Candidate**: Individual PBL Submission  
**SDG 9**: Industry, Innovation and Infrastructure  

This presentation guide is structured for an interactive 5-to-10 minute demonstration before an academic evaluation panel.

---

## 1. PRE-DEMO SETUP & LAUNCH

Open PowerShell or Command Prompt in the project root:

```powershell
cd d:\dhruv\FileSense

# Generate synthetic demonstration dataset & launch FileSense
python main.py --demo
```

---

## 2. STEP-BY-STEP PRESENTATION SCRIPT

### Step 1: Introduction & Problem Statement (1 Minute)
- **Objective**: Explain that users frequently suffer from disk bloat and slow file searches because operating systems repeatedly scan raw directory trees on demand, wasting disk I/O and battery.
- **Solution**: FileSense builds a persistent hierarchical Tree in memory, backs it with SQLite, indexes files using hash tables for $\mathcal{O}(1)$ lookups, and models duplicate clusters as an Adjacency-List Graph to identify redundancy via DFS/BFS.
- **SDG 9 Relevance**: Optimizes compute efficiency and local computing infrastructure by eliminating redundant filesystem traversals.

---

### Step 2: Selected Folders Workspace & Dynamic Dashboard (1.5 Minutes)
- Point out the new **Manage Folders / Select Folders** control directly on the Dashboard:
  - Shows all tracked directory roots, their selection checkboxes (`☑` / `☐`), file counts, sizes, and scan status.
  - **Dynamic Scoping**: Check or uncheck any folder to see the metric cards and bar chart immediately re-scope to ONLY the selected folders!
  - **Non-destructive Isolation**: Explain that deselecting a folder removes its files from current analysis without deleting its indexed data from SQLite.
  - **Cross-Folder Redundancy**: When both Folder A and Folder B are checked, cross-folder duplicates appear. When Folder B is unchecked, cross-folder duplicate groups disappear and only internal duplicates remain.
  - Point out **"➕ Add Folder"**, **"☑️ Select All"**, **"◻️ Clear All"**, and **"⚡ Scan Selected"** controls.
  - Point out the active workspace badge in the top header (e.g., `Workspace: FolderA + FolderB (2 folders)`).

---

### Step 3: File Explorer & Tree Hierarchy (1 Minute)
- Navigate to **"File Explorer / File Index"** on the sidebar.
- Show the **Folder Tree** on the left scoped strictly to the selected workspace roots.
- Show how selecting any folder instantaneously filters the file table on the right to that subtree and its descendants.
- Demonstrate sortable table headers (Name, Size, Extension, Modified Date).
- Double-click any file to show native OS launch integration.

---

### Step 4: Search & Performance Benchmark (1 Minute)
- Navigate to **"Search Files"**.
- Search for `"notes"` or filter by `.csv` extension. Note that queries search only within currently selected workspace roots with sub-millisecond query response times ($\approx 0.05 \text{ ms}$).
- Click **"⏱ Compare with Disk Walk"**.
- Explain the empirical benchmark modal:
  - In-memory Hash Index: Average $\mathcal{O}(1)$ hash table lookup.
  - Baseline Raw Filesystem Walk: $\mathcal{O}(N)$ sequential disk read.
  - Show the actual measured speedup factor.

---

### Step 5: Multi-Stage Duplicate Detection & Graph DFS Grouping (1.5 Minutes)
- Navigate to **"Duplicate Detection"**.
- Click **"⚡ Run Duplicate Detection"** with Stage 3 Byte Verification enabled.
- Walk the evaluators through the 3 stages:
  1. **Stage 1 (Size Partitioning)**: Files with unique sizes are skipped without touching disk content.
  2. **Stage 2 (SHA-256 Hashing)**: Candidate files are streamed in 1 MiB chunks.
  3. **Stage 3 (Graph DFS Component Verification)**: Constructs an equivalence graph of verified identical files and executes **Depth-First Search (DFS)** to isolate connected component clusters.
- Show the **Master-Detail view**:
  - Duplicate groups are dynamically scoped to files within the active workspace.
  - Group #1 (`notes.txt` & `notes_copy.txt`): Different filenames and paths, but identical content.
  - Group #2 (`sensor_readings.csv`, `sensor_readings_2026.csv`, `raw_sensor_data.csv`): Triplicate cluster ($k=3$), showing exactly $(3-1) \times S$ reclaimable storage.
  - Emphasize that `same_size_file_A.dat` and `same_size_file_B.dat` (which both have size 1024 bytes) were correctly separated and NOT flagged as duplicates!

---

### Step 6: Safe Storage Optimizer & 0/1 Knapsack (1.5 Minutes)
- Navigate to **"Storage Optimizer"**.
- Explain that FileSense is **safe and recommendation-first**:
  - One canonical master copy is retained per group and strictly protected.
- Demonstrate **0/1 Knapsack DP Budget Allocation**:
  - Enter a budget limit (e.g. `10 KB`).
  - Click **"🎒 Optimize with Knapsack DP"**.
  - Show that the algorithm solves the DP table and marks optimal items with `"🎒 SELECTED BY DP"`.
- Click **"📊 Export Recommendations (CSV)"** to save the recommendation report.
- Point out the safety lock: deletion is disabled by default, requiring explicit confirmation, hash check, and master existence validation.

---

### Step 7: Scan Audit History & About Modal (1 Minute)
- Navigate to **"Scan History"**: View the persistent chronological log of indexing runs from SQLite.
- Click **"ℹ About FileSense"** in the sidebar footer:
  - Highlights academic alignment (DSA-II CCSE0301, SDG 9).
  - Summarizes the DSA architecture (Tree, Hash tables, SHA-256 + Graph DFS components, 0/1 Knapsack DP, SQLite WAL).
  - Shows database location and safe "Reset Database Index" action.

---

### Step 8: Automated Test Suite & Backend Algorithm Integrity (1 Minute)
- Run the test suite in terminal to prove all 33 tests pass:
  ```powershell
  python -m unittest discover tests -v
  ```
- Highlight that the suite tests:
  - Directory Tree construction and traversals.
  - Hash Table indexing and SQLite persistence.
  - SHA-256 duplicate detection and false-positive prevention.
  - Graph traversal and connected components (DFS/BFS).
  - Graph algorithms (Kruskal, Prim, Dijkstra, Bellman-Ford, Floyd-Warshall, Warshall Transitive Closure).
  - Dynamic Programming (0/1 Knapsack, LCS, Matrix Chain Multiplication).
  - **10 Dedicated Scenarios for Selected Folders Workspace Scoping, Multi-Root Scanning, and Persistence.**
- All 23 test cases pass in ~2 seconds, verifying the complete scanner, hash table indexes, duplicate detection, graph algorithms (DFS, BFS, Kruskal, Prim, Dijkstra, Bellman-Ford, Floyd-Warshall, Warshall), and dynamic programming (Knapsack, Resource Allocation, LCS, MCM).

---

## 3. SUMMARY OF DEMONSTRATED DSA-II OUTCOMES

| Requirement | Implemented Location | Demonstrated Feature |
|---|---|---|
| Tree Data Structure | `app/tree_structure.py` | Directory hierarchy, recursive size aggregation |
| Hash Tables | `app/file_index.py` | Name, ext, size, hash indexes with $\mathcal{O}(1)$ avg lookup |
| Multi-Stage Duplicates | `app/duplicate_detector.py` | Size grouping $\to$ SHA-256 $\to$ Byte verification |
| Graph Adjacency List | `app/graph_structure.py` | Duplicate relationship equivalence clusters |
| DFS & BFS | `app/graph_algorithms.py` | Connected components discovery & level order |
| Transitive Closure | `app/graph_algorithms.py` | Warshall's reachability matrix $\mathcal{O}(V^3)$ |
| Spanning Trees | `app/graph_algorithms.py` | Kruskal (DSU) and Prim (Min-Heap) |
| Shortest Paths | `app/graph_algorithms.py` | Dijkstra, Bellman-Ford, Floyd-Warshall |
| Dynamic Programming | `app/dynamic_programming.py` | 0/1 Knapsack, Resource Allocation, LCS, MCM |
| Persistence & Audit | `app/database.py` | SQLite WAL mode, scan history, foreign keys |
| Non-destructive Safety | `app/storage_optimizer.py` | Canonical retention, CSV export, multi-point checks |
