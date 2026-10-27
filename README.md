# FileSense — Local File Intelligence & Redundancy Detection Tool

[![Course](https://img.shields.io/badge/Course-CCSE0301%20DSA--II-blue)](file:///d:/dhruv/FileSense)
[![Project](https://img.shields.io/badge/Project-PBL%20Final%20Submission-green)](file:///d:/dhruv/FileSense)
[![SDG](https://img.shields.io/badge/SDG%209-Industry%20Innovation%20%26%20Infrastructure-orange)](file:///d:/dhruv/FileSense)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-33%20Passing-brightgreen)](file:///d:/dhruv/FileSense/tests)

A high-performance desktop application for hierarchical local file indexing, multi-stage SHA-256 duplicate detection, graph-theoretic equivalence analysis, and dynamic-programming-driven storage optimization.

Built for **Data Structures and Algorithms-II (CCSE0301) Project-Based Learning (PBL)** final evaluation.

---

## TABLE OF CONTENTS
1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Core Objectives](#3-core-objectives)
4. [Feature Summary](#4-feature-summary)
5. [Technology Stack](#5-technology-stack)
6. [System Architecture](#6-system-architecture)
7. [DSA Concepts & Real-World Mapping](#7-dsa-concepts--real-world-mapping)
8. [Database Schema](#8-database-schema)
9. [Algorithms & Complexity Analysis](#9-algorithms--complexity-analysis)
10. [Installation & Requirements](#10-installation--requirements)
11. [How to Launch the Application](#11-how-to-launch-the-application)
12. [Demonstration Dataset Instructions](#12-demonstration-dataset-instructions)
13. [Running Automated Tests](#13-running-automated-tests)
14. [Known Limitations](#14-known-limitations)
15. [Future Scope](#15-future-scope)
16. [SDG 9 Relevance](#16-sdg-9-relevance)
17. [Screenshots & Visual Tour](#17-screenshots--visual-tour)

---

## 1. PROJECT OVERVIEW

Modern computer users, researchers, and software engineers frequently manage nested storage trees containing tens of thousands of local files. Standard operating system utilities repeatedly perform unindexed, brute-force disk reads whenever a user searches or attempts to find duplicate files. This causes excessive disk wear, high power consumption, and frustrating latency.

**FileSense** solves this by combining:
1. **Hierarchical Tree representation** of local folders and files in memory.
2. **Multi-criteria In-Memory Hash Tables** providing average $\mathcal{O}(1)$ query lookups (using Python's hash-map implementation with compound indexes).
3. **SQLite WAL persistence** ensuring scan indexes survive application restarts.
4. **Multi-Stage Duplicate Detection** combining size grouping, chunked 1 MiB SHA-256 streaming, and byte-for-byte verification to achieve 100% collision-proof redundancy discovery.
5. **Graph Data Structures** modeling verified duplicates as an Adjacency-List Graph, using **DFS** and **BFS** internally to partition redundant files into connected component clusters.
6. **Dynamic Programming Algorithms** utilizing the **0/1 Knapsack DP** model to recommend optimal storage reclamation actions within user-defined budgets.
7. **Comprehensive Backend Algorithm Suite** featuring implementations of Kruskal's MST (with Disjoint Set Union), Prim's MST (with Min-Heap), Dijkstra's shortest path, Bellman-Ford (negative-cycle detection), Floyd-Warshall (all-pairs shortest paths), Warshall's Transitive Closure, Longest Common Subsequence (LCS), and Matrix Chain Multiplication (MCM).

---

## 2. PROBLEM STATEMENT

When searching for files or detecting duplicates across large directories, standard utilities execute sequential disk traversals $\mathcal{O}(N)$. On large drives, opening and hashing every file causes prohibitive I/O overhead. Furthermore:
- Users frequently rename or relocate identical copies across different directories.
- Naive algorithms that rely on filename matching fail to discover true content duplicates.
- Naive algorithms that blindly hash every file waste computing power on files with unique sizes.
- Unsafe cleanup tools risk permanent data loss by not properly protecting master copies.

---

## 3. CORE OBJECTIVES

1. **Zero Unnecessary I/O**: Filter candidate duplicate files by byte size before touching file contents.
2. **Persistent Indexing**: Avoid repeated disk scans by caching directory trees in SQLite with incremental change detection.
3. **Sub-millisecond Search**: Use multiple hash-table indexes to achieve instantaneous query responses.
4. **Mathematical Rigor**: Represent duplicate relationships as equivalence graphs, analyze connected components with DFS and BFS, and formulate cleanup planning as a 0/1 Knapsack optimization problem.
5. **Safety by Design**: Guarantee non-destructive, recommendation-first workflows with canonical master retention and multi-point pre-deletion verification.
6. **Zero External Dependencies**: Run natively using the Python 3.11+ standard library without brittle installations.

---

## 4. FEATURE SUMMARY

The desktop interface is streamlined into 6 primary operational sections:
1. **Dashboard & Selected Folders Workspace**:
   - **Manage Folders / Select Folders**: Interactive root folder manager directly on the Dashboard. Add arbitrary directories, select/deselect individual roots, toggle "Select All" / "Clear Selection", scan selected folders, and view per-folder indexed files, sizes, and scan status.
   - **Dynamic Workspace Scoping**: All dashboard metric cards (Files, Folders, Size, Duplicate Groups, Reclaimable Bytes) and the interactive Bar Chart recalculate dynamically from only the selected folders. Deselecting a folder excludes its files from current calculations while keeping its SQLite records safely preserved.
   - **No Double-Counting**: If a parent directory and a subfolder are both selected, each physical file is evaluated and counted exactly once.
2. **File Explorer / File Index**: Split-pane directory folder tree and sortable table with instant subtree filtering, multi-column sorting, and OS default application launch, scoped to active workspace roots.
3. **Search Files**: In-memory compound filtering (substring, extension, min/max size, category, duplicate status) and live **Empirical Benchmark** measuring speedup against raw disk traversal.
4. **Duplicate Detection**: Multi-stage detection pipeline with customizable size thresholds, chunked SHA-256 hashing, byte verification, and **Graph DFS connected component clustering** to group identical files into equivalence clusters within active roots.
5. **Storage Optimizer**: Canonical master copy selection (oldest, newest, shortest path), **integrated 0/1 Knapsack DP budget allocation**, non-destructive CSV export, and optional verified deletion with multi-point verification.
6. **Scan History**: Full audit trail of past scan runs persisted in SQLite.

*(Note: Academic info, architecture specifications, and database reset are accessible via the compact "ℹ About FileSense" modal dialog in the sidebar footer. Dedicated backend algorithm modules for Kruskal, Prim, Dijkstra, Bellman-Ford, Floyd-Warshall, Warshall Transitive Closure, LCS, and Matrix Chain Multiplication remain preserved in `app/` and thoroughly verified by the test suite).*

---

## 5. TECHNOLOGY STACK

- **Language**: Python 3.11+
- **GUI Framework**: Tkinter and ttk (built-in standard library with custom `clam` theme styling)
- **Database**: SQLite 3 with Write-Ahead Logging (`sqlite3`)
- **Filesystem Traversal**: `os.scandir`, `pathlib.Path` (no symlink recursion)
- **File Hashing**: `hashlib` (SHA-256 with 1 MiB chunked streaming buffers)
- **Concurrency**: `threading.Thread` with thread-safe UI callbacks via `root.after`
- **Testing**: `unittest` (automated test suite)
- **External Dependencies**: **Zero mandatory external dependencies** (runs anywhere Python 3.11+ is installed)

---

## 6. SYSTEM ARCHITECTURE

For complete diagrams and component specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
FileSense/
├── main.py                     # Main application entry point & CLI
├── requirements.txt            # Project dependencies specification
├── README.md                   # Comprehensive project documentation
├── .gitignore                  # Git exclusions for databases and demo files
│
├── app/                        # Algorithmic & Storage Core
│   ├── config.py               # Constants, file categories, exclusions, formatting
│   ├── database.py             # SQLite WAL persistence layer and queries
│   ├── tree_structure.py       # N-ary TreeNode & DirectoryTree implementations
│   ├── file_index.py           # In-memory Hash Table indexes & multi-criteria search
│   ├── hashing.py              # Chunked streaming SHA-256 & byte verification
│   ├── scanner.py              # Recursive directory scanner with incremental sync
│   ├── duplicate_detector.py   # 3-stage duplicate detection pipeline
│   ├── graph_structure.py      # Adjacency-list Graph data structure
│   ├── graph_algorithms.py     # DFS, BFS, Warshall, Kruskal, Prim, Dijkstra, Bellman, Floyd
│   ├── dynamic_programming.py  # 0/1 Knapsack, Resource Allocation, LCS, MCM
│   ├── storage_optimizer.py    # Safe cleanup recommendations & CSV exporter
│   └── benchmark.py            # Empirical index vs disk walk benchmark tool
│
├── ui/                         # Desktop GUI Layer (Tkinter / ttk)
│   ├── styles.py               # Theme colors, fonts, and widget styling
│   ├── main_window.py          # Window orchestrator & persistent sidebar
│   ├── dashboard.py            # Overview dashboard & extension canvas charts
│   ├── file_explorer.py        # Folder tree & sortable file index table
│   ├── search_view.py          # Compound search & benchmark modal
│   ├── duplicates_view.py      # Duplicate detection master-detail viewer
│   ├── graph_view.py           # Interactive graph canvas & component visualizer
│   ├── optimizer_view.py       # Storage optimizer & 0/1 Knapsack planner
│   ├── algorithm_lab.py        # Dedicated DSA-II Algorithm demonstration lab
│   ├── history_view.py         # Scan audit history table
│   └── settings_view.py        # Settings, exclusions, and academic details
│
├── tests/                      # Automated Test Suite (22 Tests)
│   ├── test_tree_and_scanner.py
│   ├── test_index_and_db.py
│   ├── test_duplicates.py
│   ├── test_graph.py
│   ├── test_dynamic_programming.py
│   └── test_integration.py
│
├── scripts/                    # Helper Scripts
│   └── generate_demo_data.py   # Synthetic test dataset generator
│
└── docs/                       # Academic Documentation
    ├── ARCHITECTURE.md         # Architecture diagrams & component specs
    ├── ALGORITHMS.md           # Comprehensive complexity analysis
    └── DEMO_GUIDE.md           # Step-by-step presentation script
```

---

## 7. DSA CONCEPTS & REAL-WORLD MAPPING

| DSA Concept | Implementation | Real-World Application in FileSense |
|---|---|---|
| **N-ary Tree** | `app/tree_structure.py` | Models hierarchical nested folder structures with $\mathcal{O}(N)$ preorder and postorder traversals for bottom-up size aggregation. |
| **Hash Tables** | `app/file_index.py` | Implements in-memory dictionaries for filename, extension, size, and hash lookups achieving average $\mathcal{O}(1)$ response times. |
| **Pigeonhole Principle** | `app/duplicate_detector.py` | Files with different byte sizes cannot be duplicates; partitions candidate files in Stage 1 to eliminate non-duplicate disk I/O. |
| **Cryptographic Hashing** | `app/hashing.py` | Streaming SHA-256 hashing in 1 MiB chunks to process multi-gigabyte files without memory exhaustion. |
| **Adjacency-List Graph** | `app/graph_structure.py` | Models duplicate relationships as an undirected graph where vertices are files and edges represent verified equality. |
| **DFS (Depth-First Search)** | `app/graph_algorithms.py` | Explores branches deeply to partition the duplicate graph into connected components in $\mathcal{O}(V + E)$ time. |
| **BFS (Breadth-First Search)** | `app/graph_algorithms.py` | Level-by-level queue traversal computing graph diameter and shortest hops in unweighted graphs. |
| **Disjoint Set Union (DSU)** | `app/graph_algorithms.py` | Implements Path Compression and Union by Rank for Kruskal's MST running in $\mathcal{O}(E \log E)$ time. |
| **Min-Heap Priority Queue** | `app/graph_algorithms.py` | Implements Prim's MST and Dijkstra's algorithm running in $\mathcal{O}((V + E) \log V)$ time. |
| **0/1 Knapsack DP** | `app/dynamic_programming.py` | Solves storage cleanup budget allocation by finding the optimal combination of redundant files to delete under a size limit. |
| **All-Pairs DP** | `app/graph_algorithms.py` | Implements Warshall's Transitive Closure and Floyd-Warshall $\mathcal{O}(V^3)$ reachability and distance matrices. |
| **Longest Common Subsequence** | `app/dynamic_programming.py` | Computes text similarity across text snippets using an $\mathcal{O}(m \cdot n)$ dynamic programming table. |
| **Matrix Chain Multiplication** | `app/dynamic_programming.py` | Solves optimal matrix parenthesization minimizing scalar operations in $\mathcal{O}(n^3)$ time. |

---

## 8. DATABASE SCHEMA

The SQLite database (`data/filesense.db`) consists of 5 relational tables:

1. **`folders`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `parent_id INTEGER`
   - `name TEXT NOT NULL`
   - `path TEXT UNIQUE NOT NULL`
   - `indexed_at TEXT NOT NULL`
2. **`files`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `parent_id INTEGER REFERENCES folders(id)`
   - `filename TEXT NOT NULL`
   - `path TEXT UNIQUE NOT NULL`
   - `type TEXT NOT NULL`
   - `extension TEXT NOT NULL`
   - `size INTEGER NOT NULL`
   - `created_at TEXT`
   - `modified_at TEXT`
   - `content_hash TEXT`
   - `hash_status TEXT DEFAULT 'PENDING'`
   - `indexed_at TEXT NOT NULL`
3. **`scan_history`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `root_path TEXT NOT NULL`
   - `started_at TEXT NOT NULL`
   - `completed_at TEXT`
   - `files_scanned INTEGER DEFAULT 0`
   - `folders_scanned INTEGER DEFAULT 0`
   - `bytes_scanned INTEGER DEFAULT 0`
   - `status TEXT NOT NULL`
   - `error_count INTEGER DEFAULT 0`
4. **`duplicate_groups`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `group_hash TEXT UNIQUE NOT NULL`
   - `file_size INTEGER NOT NULL`
   - `file_count INTEGER NOT NULL`
   - `reclaimable_size INTEGER NOT NULL`
   - `created_at TEXT NOT NULL`
5. **`duplicate_group_files`**:
   - `group_id INTEGER REFERENCES duplicate_groups(id)`
   - `file_id INTEGER REFERENCES files(id)`
   - `is_canonical INTEGER DEFAULT 0`
   - `PRIMARY KEY (group_id, file_id)`

---

## 9. ALGORITHMS & COMPLEXITY ANALYSIS

Detailed mathematical analysis is available in [docs/ALGORITHMS.md](docs/ALGORITHMS.md).

### Summary Table

| Algorithm | Method / Data Structure | Time Complexity | Auxiliary Space |
|---|---|---|---|
| Directory Traversal | Recursive $N$-ary Tree | $\mathcal{O}(N)$ | $\mathcal{O}(H)$ |
| Filename / Ext Lookup | In-Memory Hash Table | $\mathcal{O}(1)$ avg | $\mathcal{O}(N)$ |
| Duplicate Detection Stage 1 | Size Partitioning Map | $\mathcal{O}(N)$ | $\mathcal{O}(N)$ |
| Duplicate Detection Stage 2 | Chunked SHA-256 Hashing | $\mathcal{O}(B / \text{chunk})$ | $\mathcal{O}(1)$ |
| Duplicate Detection Stage 3 | Byte-by-Byte Verification | $\mathcal{O}(S / \text{chunk})$ | $\mathcal{O}(1)$ |
| DFS (Connected Components)| Adjacency List + Visited Set | $\mathcal{O}(V + E)$ | $\mathcal{O}(V)$ |
| BFS (Level Traversal) | Adjacency List + FIFO Queue | $\mathcal{O}(V + E)$ | $\mathcal{O}(V)$ |
| Warshall Transitive Closure | 3 Nested Loops DP | $\mathcal{O}(V^3)$ | $\mathcal{O}(V^2)$ |
| Kruskal's MST | Disjoint Set Union (DSU) | $\mathcal{O}(E \log E)$ | $\mathcal{O}(V)$ |
| Prim's MST | Min-Heap Priority Queue | $\mathcal{O}(E \log V)$ | $\mathcal{O}(V + E)$ |
| Dijkstra's Shortest Path | Min-Heap Priority Queue | $\mathcal{O}((V + E) \log V)$ | $\mathcal{O}(V)$ |
| Bellman-Ford | Edge Relaxation ($|V|-1$ passes)| $\mathcal{O}(V \cdot E)$ | $\mathcal{O}(V)$ |
| Floyd-Warshall All-Pairs | Dynamic Programming Matrix | $\mathcal{O}(V^3)$ | $\mathcal{O}(V^2)$ |
| 0/1 Knapsack Optimization | Dynamic Programming Table | $\mathcal{O}(n \cdot W)$ | $\mathcal{O}(n \cdot W)$ |
| Longest Common Subsequence | Dynamic Programming Matrix | $\mathcal{O}(m \cdot n)$ | $\mathcal{O}(m \cdot n)$ |
| Matrix Chain Multiplication| Dynamic Programming Matrix | $\mathcal{O}(n^3)$ | $\mathcal{O}(n^2)$ |

---

## 10. INSTALLATION & REQUIREMENTS

### Prerequisites
- Operating System: Windows 10/11 (or Linux / macOS)
- Python Version: **Python 3.11, 3.12, 3.13, or 3.14+**
- Tkinter: Pre-installed with standard Windows Python distributions.

### Clone or Download
```powershell
cd d:\dhruv\FileSense
```

No external pip packages are mandatory. To install optional packages for pytest:
```powershell
pip install -r requirements.txt
```

---

## 11. HOW TO LAUNCH THE APPLICATION

### Standard Launch
```powershell
python main.py
```

### Launch with Synthetic Demo Dataset Generated Automatically
```powershell
python main.py --demo
```

### Launch and Scan a Specific Directory
```powershell
python main.py --scan "C:\Users\username\Documents"
```

### Run Automated Tests from CLI
```powershell
python main.py --test
```

---

## 12. DEMONSTRATION DATASET INSTRUCTIONS

FileSense includes a built-in synthetic dataset generator that creates a dedicated folder: `demo_data/`.

To generate it directly from terminal:
```powershell
python scripts/generate_demo_data.py
```
Or simply click the **"🧪 Generate Demo Data"** button in the FileSense Dashboard.

The generator creates:
- Exact duplicate pair: `documents/notes.txt` and `backups/notes_copy.txt` (different names and paths, identical content).
- Exact duplicate pair: `documents/assignment.txt` and `backups/assignment_backup.txt`.
- Exact triplicate group: `data/sensor_readings.csv`, `backups/sensor_readings_2026.csv`, and `reports/raw_sensor_data.csv` (3 identical copies; reclaimable size = $(3 - 1) \times S$).
- Code duplicates: `code/algorithm_utils.py` and `backups/algorithm_utils_v1.py`.
- **False-Positive Collision Test**: `documents/same_size_file_A.dat` and `reports/same_size_file_B.dat` (both are exactly 1024 bytes, but have completely different contents; verifies that Stage 1 size grouping correctly filters to Stage 2 where SHA-256 rejects them).
- Empty files: `backups/empty_log_1.log` and `reports/empty_log_2.log` (0-byte duplicate test).
- Unique files of various sizes and extensions (`.pdf`, `.png`, `.zip`, `.py`, `.md`).

---

## 13. RUNNING AUTOMATED TESTS

The test suite covers 23 comprehensive tests across 6 test modules:
1. Directory tree construction & traversals
2. Recursive discovery of nested files
3. In-memory hash-table indexing & compound search
4. SQLite persistence & scan history
5. Exact duplicate detection with differing filenames
6. Correct rejection of same-sized files with different content
7. Correct handling of 0-byte empty files
8. DFS connected components
9. BFS connected components & level distances
10. Disconnected graph handling
11. Kruskal's MST with Disjoint Set Union
12. Prim's MST with Min-Heap Priority Queue
13. Dijkstra's shortest path
14. Bellman-Ford negative-cycle detection
15. Floyd-Warshall all-pairs distance matrix
16. 0/1 Knapsack optimal value & item reconstruction
17. Longest Common Subsequence (LCS) & DP table
18. Matrix Chain Multiplication optimal parenthesization
19. Missing & inaccessible directory handling
20. Incremental indexing after file modifications
21. Warshall's Transitive Closure reachability matrix
22. Complete End-to-End integration pipeline
23. MainWindow view registration and navigation lifecycle

### Execute All Tests
```powershell
python -m unittest discover tests -v
```

**Result**: 23 tests passing in ~2.6 seconds with 0 errors.

---

## 14. KNOWN LIMITATIONS

1. **In-Memory Scale**: The in-memory hash tables are designed to handle directories up to approximately 250,000 files in memory. For enterprise volumes exceeding millions of files, queries should page directly from SQLite using cursor iterators.
2. **Symbolic Links**: FileSense intentionally does not follow symbolic links by default to prevent infinite cyclic recursion.
3. **OS-Level File Locks**: Files locked by active processes (e.g., active database files or running executables) will be logged as inaccessible during hashing and skipped gracefully without crashing.

---

## 15. FUTURE SCOPE

1. **Perceptual Image Hashing**: Incorporate pHash / dHash algorithms to detect visually similar images even after minor resizing or compression.
2. **Hard Link Deduplication**: Offer an option to replace redundant copies on NTFS with filesystem hard links, saving storage without changing paths.
3. **Background Real-time File Watcher**: Integrate `ReadDirectoryChangesW` (Windows API) to update the SQLite index automatically when files are created or modified.

---

## 16. SDG 9 RELEVANCE

**United Nations Sustainable Development Goal 9: Industry, Innovation and Infrastructure**
- **Target 9.4 & 9.5**: Upgrade technological capabilities and improve computing resource efficiency.
- **Direct Alignment**: By replacing repetitive, unindexed, brute-force disk scanning with in-memory tree hierarchies and hash-table indexing, FileSense substantially reduces redundant disk read operations, lowers device power consumption, and optimizes digital storage infrastructure.

---

## 17. SCREENSHOTS & VISUAL TOUR

Screenshots can be saved in the `docs/screenshots/` directory.

To capture screenshots during demonstration:
1. Launch the application: `python main.py --demo`
2. Press `Alt + PrtScn` on Windows to capture the active window.
3. Paste and save images to:
   - `docs/screenshots/01_overview_dashboard.png` — Overview Dashboard with extension canvas bar chart and metric cards.
   - `docs/screenshots/02_file_explorer.png` — Split-pane directory tree and sortable table.
   - `docs/screenshots/03_search_benchmark.png` — Multi-criteria search and live empirical benchmark modal.
   - `docs/screenshots/04_duplicate_detection.png` — Duplicate clusters with master-detail view.
   - `docs/screenshots/05_storage_optimizer.png` — 0/1 Knapsack DP budget allocation and CSV export.
   - `docs/screenshots/06_scan_history.png` — Chronological audit trail from SQLite.
   - `docs/screenshots/07_about_dialog.png` — Academic info, DSA architecture, and index maintenance modal.

---

*FileSense — Built for Excellence in Data Structures and Algorithms-II (CCSE0301).*
