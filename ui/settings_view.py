"""
Settings and Academic Information Screen for FileSense.
Displays system parameters, exclusion rules, SQLite configuration,
and DSA-II course alignment.
"""

import sys
import platform
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from app.config import (
    APP_NAME,
    APP_VERSION,
    COURSE_NAME,
    COURSE_CODE,
    SDG_ALIGNMENT,
    DEFAULT_DB_PATH,
    DEFAULT_EXCLUDED_NAMES,
    DEFAULT_EXCLUDED_EXTENSIONS,
    HASH_ALGORITHM,
    HASH_CHUNK_SIZE,
    format_bytes,
)
from ui.styles import COLORS, FONTS


class SettingsView(ttk.Frame):
    """
    Settings, Architecture specifications, and Academic Project info.
    """

    def __init__(self, parent: tk.Widget, on_clear_database: Callable[[], None]):
        super().__init__(parent)
        self.on_clear_database = on_clear_database
        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Application Settings & Academic Alignment", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text=f"{COURSE_NAME} ({COURSE_CODE}) PBL Submission • {SDG_ALIGNMENT}",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Scrollable container
        canvas = tk.Canvas(self, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_win = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))

        # Card 1: Academic & Project Metadata
        c1 = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        c1.pack(fill=tk.X, padx=5, pady=(0, 15))

        tk.Label(c1, text="Academic Project Alignment", font=FONTS["title_medium"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))

        meta_info = (
            f"• Project Name: {APP_NAME} v{APP_VERSION}\n"
            f"• Course: {COURSE_NAME} ({COURSE_CODE}) — Final PBL Project\n"
            f"• UN Sustainable Development Goal: {SDG_ALIGNMENT}\n"
            f"• Target Users: Students, researchers, and engineers managing large nested local directories.\n"
            f"• Core Problem: Mitigating redundant disk I/O and unindexed file traversals through persistent indexes\n"
            f"  and evidence-based duplicate detection."
        )
        tk.Label(c1, text=meta_info, justify="left", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")

        # Card 2: DSA Concepts Implemented
        c2 = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        c2.pack(fill=tk.X, padx=5, pady=(0, 15))

        tk.Label(c2, text="Implemented Data Structures & Algorithms", font=FONTS["title_medium"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))

        dsa_info = (
            "1. Tree Data Structure: N-ary DirectoryTree for folder/file hierarchy & recursive size aggregation.\n"
            "2. Hash Tables: Average O(1) in-memory dictionaries for filename, extension, size, and SHA-256 indexes.\n"
            "3. Graph Data Structure: Adjacency List representing duplicate equivalence cliques.\n"
            "4. Graph Traversal: DFS & BFS for connected components discovery (O(V + E) time, O(V) space).\n"
            "5. Transitive Closure: Warshall's reachability algorithm (O(V^3) time, O(V^2) space).\n"
            "6. Spanning Trees: Kruskal's MST (Disjoint Set Union) & Prim's MST (Min-Heap Priority Queue).\n"
            "7. Shortest Paths: Dijkstra (Min-Heap), Bellman-Ford (Negative Cycle detection), Floyd-Warshall.\n"
            "8. Dynamic Programming: 0/1 Knapsack (Storage cleanup), Resource Allocation, LCS, Matrix Chain."
        )
        tk.Label(c2, text=dsa_info, justify="left", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")

        # Card 3: Storage Engine & Pipeline Configuration
        c3 = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        c3.pack(fill=tk.X, padx=5, pady=(0, 15))

        tk.Label(c3, text="Engine Parameters & Environment", font=FONTS["title_medium"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))

        sys_info = (
            f"• Database Path: {DEFAULT_DB_PATH}\n"
            f"• SQLite Mode: Write-Ahead Logging (WAL), Foreign Keys ON, Synchronous NORMAL\n"
            f"• Cryptographic Hash: {HASH_ALGORITHM.upper()} streaming buffer size {format_bytes(HASH_CHUNK_SIZE)}\n"
            f"• Python Environment: {platform.python_implementation()} {sys.version.split()[0]} on {platform.system()} {platform.release()}\n"
            f"• SQLite Version: {sqlite3.sqlite_version}\n"
            f"• Excluded Names: {', '.join(sorted(DEFAULT_EXCLUDED_NAMES)[:8])}...\n"
            f"• Excluded Extensions: {', '.join(sorted(DEFAULT_EXCLUDED_EXTENSIONS))}"
        )
        tk.Label(c3, text=sys_info, justify="left", font=FONTS["mono"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(anchor="w")

        # Card 4: Database Maintenance
        c4 = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        c4.pack(fill=tk.X, padx=5, pady=(0, 20))

        tk.Label(c4, text="Database Maintenance", font=FONTS["title_medium"], bg=COLORS["bg_card"], fg=COLORS["danger"]).pack(anchor="w", pady=(0, 4))
        tk.Label(
            c4,
            text="Wipe all persistent indexing records, duplicate groups, and scan logs from filesense.db.",
            font=FONTS["body_small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(c4, text="⚠️ Wipe All Database Records", style="Danger.TButton", command=self._confirm_clear).pack(anchor="w")

    def _confirm_clear(self) -> None:
        confirm = messagebox.askyesno(
            "Confirm Database Reset",
            "Are you sure you want to clear all indexed files, folders, and duplicate groups from SQLite?\n\nThis will not delete any files on your disk.",
            icon="warning",
        )
        if confirm:
            self.on_clear_database()
            messagebox.showinfo("Database Cleared", "The database index has been completely reset.")
