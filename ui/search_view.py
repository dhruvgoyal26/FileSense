"""
Search Screen and Empirical Benchmark Interface.
Performs lightning-fast in-memory hash index searches and compares performance
against raw filesystem traversal.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
from app.config import format_bytes
from app.file_index import FileIndex
from app.benchmark import benchmark_search_comparison
from ui.styles import COLORS, FONTS


class SearchView(ttk.Frame):
    """
    Search Files view with compound filters and live performance benchmarking.
    """

    def __init__(
        self,
        parent: tk.Widget,
        file_index: FileIndex,
        get_current_root: Callable[[], Optional[str]],
    ):
        super().__init__(parent)
        self.file_index = file_index
        self.get_current_root = get_current_root
        self.current_results: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        # Header Toolbar
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Advanced File Search & Performance Benchmark", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="In-memory hash table lookups with compound filtering and empirical speedup analysis.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Action Buttons
        btn_box = ttk.Frame(header)
        btn_box.pack(side=tk.RIGHT)
        ttk.Button(btn_box, text="⚡ Run Search", style="Primary.TButton", command=self.execute_search).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="⏱ Compare with Disk Walk", style="Secondary.TButton", command=self._run_benchmark).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="🔄 Reset Filters", style="Secondary.TButton", command=self._reset_filters).pack(side=tk.LEFT, padx=3)

        # Filters Card
        filter_card = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=12)
        filter_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Row 1: Filename query & Extension
        r1 = tk.Frame(filter_card, bg=COLORS["bg_card"])
        r1.pack(fill=tk.X, pady=(0, 8))

        tk.Label(r1, text="Filename / Substring:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", lambda *a: self.execute_search())
        q_entry = ttk.Entry(r1, textvariable=self.query_var, width=28)
        q_entry.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(r1, text="Extension:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.ext_var = tk.StringVar()
        self.ext_var.trace_add("write", lambda *a: self.execute_search())
        ext_entry = ttk.Entry(r1, textvariable=self.ext_var, width=12)
        ext_entry.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(r1, text="Category:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(
            r1,
            textvariable=self.cat_var,
            values=["All", "Document", "Image", "Code", "Archive", "Audio", "Video", "Other"],
            state="readonly",
            width=12,
        )
        cat_combo.bind("<<ComboboxSelected>>", lambda e: self.execute_search())
        cat_combo.pack(side=tk.LEFT, padx=(0, 20))

        self.dup_only_var = tk.BooleanVar(value=False)
        chk_dup = ttk.Checkbutton(r1, text="Duplicates Only", variable=self.dup_only_var, command=self.execute_search)
        chk_dup.pack(side=tk.LEFT)

        # Row 2: Size Ranges
        r2 = tk.Frame(filter_card, bg=COLORS["bg_card"])
        r2.pack(fill=tk.X)

        tk.Label(r2, text="Min Size (KB):", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.min_size_var = tk.StringVar()
        min_entry = ttk.Entry(r2, textvariable=self.min_size_var, width=10)
        min_entry.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(r2, text="Max Size (KB):", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.max_size_var = tk.StringVar()
        max_entry = ttk.Entry(r2, textvariable=self.max_size_var, width=10)
        max_entry.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(r2, text="Apply Size Range", style="Secondary.TButton", command=self.execute_search).pack(side=tk.LEFT)

        # Execution telemetry banner
        self.telemetry_bar = tk.Frame(self, bg=COLORS["bg_card_secondary"], padx=14, pady=6, highlightbackground=COLORS["border_light"], highlightthickness=1)
        self.telemetry_bar.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_telemetry = tk.Label(
            self.telemetry_bar,
            text="Search Ready • 0 results found (0.00 ms)",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
        )
        self.lbl_telemetry.pack(side=tk.LEFT)

        # Results Table
        table_frame = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        cols = ("filename", "extension", "size", "type", "modified_at", "duplicate", "path")
        self.results_table = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")

        col_widths = {
            "filename": 220,
            "extension": 70,
            "size": 90,
            "type": 90,
            "modified_at": 140,
            "duplicate": 90,
            "path": 320,
        }

        col_titles = {
            "filename": "Filename",
            "extension": "Ext",
            "size": "Size",
            "type": "Category",
            "modified_at": "Modified",
            "duplicate": "Duplicate?",
            "path": "Full Location Path",
        }

        for c in cols:
            self.results_table.heading(c, text=col_titles[c])
            self.results_table.column(c, width=col_widths[c], anchor="w" if c not in ("size", "duplicate") else "e")

        self.results_table.column("duplicate", anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_table.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results_table.xview)
        self.results_table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.results_table.bind("<Double-1>", lambda e: self._open_selected())

        self.results_table.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _reset_filters(self) -> None:
        self.query_var.set("")
        self.ext_var.set("")
        self.cat_var.set("All")
        self.min_size_var.set("")
        self.max_size_var.set("")
        self.dup_only_var.set(False)
        self.execute_search()

    def execute_search(self) -> None:
        """Run compound search using in-memory hash tables."""
        import time

        query = self.query_var.get().strip()
        ext = self.ext_var.get().strip()
        cat = self.cat_var.get()
        dup_only = self.dup_only_var.get()

        min_bytes = None
        max_bytes = None

        try:
            if self.min_size_var.get().strip():
                min_bytes = int(float(self.min_size_var.get().strip()) * 1024)
        except ValueError:
            pass

        try:
            if self.max_size_var.get().strip():
                max_bytes = int(float(self.max_size_var.get().strip()) * 1024)
        except ValueError:
            pass

        t0 = time.perf_counter()
        results = self.file_index.multi_criteria_search(
            query=query if query else None,
            extension=ext if ext else None,
            min_size=min_bytes,
            max_size=max_bytes,
            category=cat if cat != "All" else None,
            duplicates_only=dup_only,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.current_results = results

        # Update table
        for item in self.results_table.get_children():
            self.results_table.delete(item)

        total_bytes = sum(r["size"] for r in results)
        self.lbl_telemetry.config(
            text=f"Found {len(results):,} files  |  Total: {format_bytes(total_bytes)}  |  Query Time: {elapsed_ms:.3f} ms"
        )

        for r in results:
            dup_tag = "⚠️ Duplicate" if r.get("is_duplicate") else "—"
            mod_str = (r.get("modified_at") or "")[:19].replace("T", " ")
            self.results_table.insert(
                "",
                tk.END,
                values=(
                    r["filename"],
                    r.get("extension", ""),
                    format_bytes(r["size"]),
                    r.get("type", "Other"),
                    mod_str,
                    dup_tag,
                    r["path"],
                ),
            )

    def _run_benchmark(self) -> None:
        """Execute live empirical benchmark comparing index vs disk walk."""
        root = self.get_current_root()
        if not root or not os.path.isdir(root):
            messagebox.showinfo("Benchmark Notice", "Please scan or select a root directory first to run disk comparison.")
            return

        query = self.query_var.get().strip() or "test"
        bench_data = benchmark_search_comparison(root, self.file_index, query)

        # Show benchmark popup modal
        bench_win = tk.Toplevel(self)
        bench_win.title("Search Performance Benchmark — DSA Analysis")
        bench_win.geometry("580x420")
        bench_win.configure(bg=COLORS["bg_main"])
        bench_win.transient(self.winfo_toplevel())

        pad_f = ttk.Frame(bench_win, padding=20)
        pad_f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(pad_f, text="Empirical Complexity & Performance Comparison", font=FONTS["title_medium"]).pack(anchor="w", pady=(0, 6))

        info_text = (
            f"Query: '{query}'\n"
            f"Target Root: {root}\n\n"
            f"1. FileSense In-Memory Hash Index (O(1) Avg Lookup):\n"
            f"   • Response Time: {bench_data['indexed_time_ms']:.3f} ms\n"
            f"   • Matches Found: {bench_data['indexed_match_count']}\n\n"
            f"2. Baseline Raw Filesystem Walk (O(N) Disk I/O Traversal):\n"
            f"   • Response Time: {bench_data['raw_time_ms']:.3f} ms\n"
            f"   • Files Inspected on Disk: {bench_data['raw_scanned_files']}\n"
            f"   • Matches Found: {bench_data['raw_match_count']}\n\n"
            f"Speedup Factor: {bench_data['speedup_factor']:.1f}x Faster\n\n"
            f"{bench_data['explanation']}"
        )

        msg_box = tk.Text(pad_f, wrap="word", height=14, font=FONTS["mono"], bg=COLORS["bg_card"], fg=COLORS["text_primary"], relief="solid", borderwidth=1, padx=10, pady=10)
        msg_box.insert("1.0", info_text)
        msg_box.configure(state="disabled")
        msg_box.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        ttk.Button(pad_f, text="Close", style="Primary.TButton", command=bench_win.destroy).pack(anchor="e")

    def _open_selected(self) -> None:
        sel = self.results_table.selection()
        if not sel:
            return
        row = self.results_table.item(sel[0], "values")
        filepath = row[6]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found on disk:\n{filepath}")
            return
        try:
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Cannot Open File", f"Error:\n{e}")
