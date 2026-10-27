"""
Safe Storage Optimizer Screen for FileSense.
Generates safe redundancy cleanup recommendations, connects to 0/1 Knapsack DP
for budget-constrained optimization, supports CSV export, and enforces
strict integrity safeguards.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Any, Callable
from app.config import format_bytes
from app.storage_optimizer import StorageOptimizer
from ui.styles import COLORS, FONTS


class OptimizerView(ttk.Frame):
    """
    Storage Optimizer Screen with Safe Non-Destructive Recommendations,
    0/1 Knapsack DP budget allocation, and CSV export.
    """

    def __init__(
        self,
        parent: tk.Widget,
        optimizer: StorageOptimizer,
        on_refresh_data: Callable[[], None],
        get_selected_roots: Optional[Callable[[], List[str]]] = None,
    ):
        super().__init__(parent)
        self.optimizer = optimizer
        self.on_refresh_data = on_refresh_data
        self.get_selected_roots = get_selected_roots

        self.current_plan: Optional[Dict[str, Any]] = None
        self.candidates: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        # Header Toolbar
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Safe Storage Cleanup Optimizer", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Evidence-based redundancy resolution with canonical retention and 0/1 Knapsack DP budget planning.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Action Buttons
        btn_box = ttk.Frame(header)
        btn_box.pack(side=tk.RIGHT)
        ttk.Button(btn_box, text="📊 Export Recommendations (CSV)", style="Primary.TButton", command=self._export_csv).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="🔄 Recalculate Plan", style="Secondary.TButton", command=self.load_plan).pack(side=tk.LEFT, padx=3)

        # Controls & Knapsack Budget Card
        ctrl_card = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=14, pady=10)
        ctrl_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Row 1: Canonical strategy
        r1 = tk.Frame(ctrl_card, bg=COLORS["bg_card"])
        r1.pack(fill=tk.X, pady=(0, 8))

        tk.Label(r1, text="Canonical Copy Rule:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.strategy_var = tk.StringVar(value="oldest")
        strat_combo = ttk.Combobox(
            r1,
            textvariable=self.strategy_var,
            values=["oldest", "newest", "shortest_path"],
            state="readonly",
            width=16,
        )
        strat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_plan())
        strat_combo.pack(side=tk.LEFT, padx=(0, 20))

        # 0/1 Knapsack Budget Inputs
        tk.Label(r1, text="Storage Reclamation Budget:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(side=tk.LEFT, padx=(0, 8))
        self.budget_var = tk.StringVar(value="500")
        budget_entry = ttk.Entry(r1, textvariable=self.budget_var, width=8)
        budget_entry.pack(side=tk.LEFT, padx=(0, 6))

        self.budget_unit_var = tk.StringVar(value="KB")
        unit_combo = ttk.Combobox(r1, textvariable=self.budget_unit_var, values=["B", "KB", "MB", "GB"], width=6, state="readonly")
        unit_combo.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(r1, text="🎒 Optimize with Knapsack DP", style="Primary.TButton", command=self._run_knapsack_budget).pack(side=tk.LEFT)

        # Safety & Deletion Options (Disabled by default)
        r2 = tk.Frame(ctrl_card, bg=COLORS["bg_card"])
        r2.pack(fill=tk.X)

        self.enable_deletion_var = tk.BooleanVar(value=False)
        chk_enable = ttk.Checkbutton(
            r2,
            text="Enable optional verified cleanup (Safety locked by default)",
            variable=self.enable_deletion_var,
            command=self._toggle_delete_button,
        )
        chk_enable.pack(side=tk.LEFT)

        self.btn_delete = ttk.Button(
            r2,
            text="🗑 Delete Selected Redundant Copy",
            style="Danger.TButton",
            state="disabled",
            command=self._execute_verified_deletion,
        )
        self.btn_delete.pack(side=tk.RIGHT, padx=5)

        # Summary Banner
        self.banner = tk.Frame(self, bg=COLORS["bg_card_secondary"], padx=14, pady=8, highlightbackground=COLORS["border_light"], highlightthickness=1)
        self.banner.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_stats = tk.Label(
            self.banner,
            text="0 redundant cleanup candidates | 0 B reclaimable",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
        )
        self.lbl_stats.pack(side=tk.LEFT)

        self.lbl_knapsack_result = tk.Label(
            self.banner,
            text="Knapsack DP: Ready to optimize",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["secondary"],
        )
        self.lbl_knapsack_result.pack(side=tk.RIGHT)

        # Recommendations Table
        table_frame = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        cols = ("action", "filename", "size", "redundant_path", "canonical_path", "group_id")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.table.heading("action", text="Recommendation")
        self.table.heading("filename", text="Filename")
        self.table.heading("size", text="Reclaimable Size")
        self.table.heading("redundant_path", text="Redundant Candidate Path (Target)")
        self.table.heading("canonical_path", text="Retained Master Copy (Safe)")
        self.table.heading("group_id", text="Group #")

        self.table.column("action", width=140, anchor="center")
        self.table.column("filename", width=180, anchor="w")
        self.table.column("size", width=110, anchor="e")
        self.table.column("redundant_path", width=320, anchor="w")
        self.table.column("canonical_path", width=320, anchor="w")
        self.table.column("group_id", width=70, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.table.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _toggle_delete_button(self) -> None:
        """Enable or disable delete button based on checkbox."""
        if self.enable_deletion_var.get():
            self.btn_delete.configure(state="normal")
        else:
            self.btn_delete.configure(state="disabled")

    def load_plan(self) -> None:
        """Generate fresh cleanup recommendations."""
        strat = self.strategy_var.get()
        roots = self.get_selected_roots() if self.get_selected_roots else None
        self.current_plan = self.optimizer.generate_cleanup_plan(canonical_strategy=strat, root_paths=roots)
        self.candidates = self.current_plan["cleanup_candidates"]

        # Update table
        for item in self.table.get_children():
            self.table.delete(item)

        total_size = self.current_plan["total_reclaimable_bytes"]
        total_files = self.current_plan["total_redundant_files"]
        self.lbl_stats.config(
            text=f"{total_files} redundant cleanup candidates identified  |  Total potential savings: {format_bytes(total_size)}"
        )

        for c in self.candidates:
            self.table.insert(
                "",
                tk.END,
                values=(
                    "Safe to Remove",
                    c["filename"],
                    format_bytes(c["size"]),
                    c["path"],
                    c["canonical_path"],
                    c["group_id"],
                ),
            )

    def _run_knapsack_budget(self) -> None:
        """Solve 0/1 Knapsack DP for user-defined storage budget."""
        if not self.candidates:
            self.load_plan()
        if not self.candidates:
            messagebox.showinfo("Knapsack Notice", "No duplicate candidates available to optimize.")
            return

        try:
            val = float(self.budget_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Budget", "Please enter a valid numeric budget value.")
            return

        unit = self.budget_unit_var.get()
        multipliers = {"B": 1, "KB": 1024, "MB": 1024 * 1024, "GB": 1024 * 1024 * 1024}
        budget_bytes = int(val * multipliers.get(unit, 1024))

        dp_res = self.optimizer.optimize_with_knapsack_budget(self.candidates, budget_bytes)

        selected_paths = {it["path"] for it in dp_res["selected_items"]}

        # Update table markings
        for item_id in self.table.get_children():
            row_vals = list(self.table.item(item_id, "values"))
            r_path = row_vals[3]
            if r_path in selected_paths:
                row_vals[0] = "🎒 SELECTED BY DP"
            else:
                row_vals[0] = "Excess (Outside Budget)"
            self.table.item(item_id, values=row_vals)

        self.lbl_knapsack_result.config(
            text=(
                f"DP Selected: {dp_res['selected_count']} files  |  "
                f"Allocated: {format_bytes(dp_res['total_selected_size'])} / {format_bytes(budget_bytes)}  |  "
                f"Time: {dp_res['execution_time_ms']:.2f} ms"
            )
        )

        messagebox.showinfo(
            "Knapsack Optimization Complete",
            f"0/1 Knapsack Algorithm successfully solved!\n\n"
            f"Budget Limit: {format_bytes(budget_bytes)}\n"
            f"Selected Actions: {dp_res['selected_count']} independent redundant files\n"
            f"Total Reclaimed: {format_bytes(dp_res['total_selected_size'])}\n"
            f"DP Optimal Utility Value: {dp_res['optimal_value']}\n"
            f"Execution Time: {dp_res['execution_time_ms']:.3f} ms\n\n"
            f"Selected items are tagged with '🎒 SELECTED BY DP' in the table.",
        )

    def _export_csv(self) -> None:
        """Export cleanup plan recommendations to CSV."""
        if not self.candidates:
            self.load_plan()
        if not self.candidates:
            messagebox.showinfo("Export", "No cleanup recommendations to export.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="filesense_cleanup_recommendations.csv",
        )
        if not save_path:
            return

        rows = self.optimizer.export_recommendations_csv(self.candidates, save_path)
        messagebox.showinfo("Export Successful", f"Saved {rows} cleanup recommendations to:\n{save_path}")

    def _execute_verified_deletion(self) -> None:
        """Safely remove a confirmed redundant copy with rigorous validation."""
        sel = self.table.selection()
        if not sel:
            messagebox.showinfo("Select Candidate", "Please select a candidate file from the table to delete.")
            return

        row = self.table.item(sel[0], "values")
        filename = row[1]
        target_path = row[3]
        canonical_path = row[4]

        # Find candidate details
        cand = next((c for c in self.candidates if c["path"] == target_path), None)
        if not cand:
            messagebox.showerror("Error", "Candidate metadata missing.")
            return

        # Double confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Verified Deletion",
            f"Are you sure you want to delete this confirmed duplicate?\n\n"
            f"File: {filename}\n"
            f"Path: {target_path}\n\n"
            f"The canonical master copy will be safely retained at:\n"
            f"{canonical_path}\n\n"
            f"FileSense will verify SHA-256 hashes and byte-equality before removing.",
            icon="warning",
        )
        if not confirm:
            return

        success, msg = self.optimizer.safe_delete_file(
            target_path=target_path,
            expected_size=cand["size"],
            expected_hash=cand["group_hash"],
            canonical_path=canonical_path,
        )

        if success:
            messagebox.showinfo("Deletion Complete", msg)
            self.on_refresh_data()
            self.load_plan()
        else:
            messagebox.showerror("Safety Abort", f"Operation aborted by safety checks:\n{msg}")
