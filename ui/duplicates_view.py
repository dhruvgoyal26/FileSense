"""
Duplicate Detection Screen for FileSense.
Coordinates the multi-stage duplicate detection pipeline,
displays duplicate clusters, canonical copies, and accurate savings.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
from app.config import format_bytes
from ui.styles import COLORS, FONTS


class DuplicatesView(ttk.Frame):
    """
    Duplicate Detection view with controls, summary banners,
    and master-detail group viewer.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_run_detection: Callable[[int, Optional[str], bool], None],
        get_duplicate_groups: Callable[[], List[Dict[str, Any]]],
        on_navigate_to_optimizer: Callable[[], None],
        on_navigate_to_graph: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_run_detection = on_run_detection
        self.get_duplicate_groups = get_duplicate_groups
        self.on_navigate_to_optimizer = on_navigate_to_optimizer
        self.on_navigate_to_graph = on_navigate_to_graph

        self.groups_data: List[Dict[str, Any]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        # Header Toolbar
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Multi-Stage Duplicate Detection", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Stage 1: Size grouping  ➜  Stage 2: Chunked SHA-256  ➜  Stage 3: Graph DFS component verification",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Action Buttons
        btn_box = ttk.Frame(header)
        btn_box.pack(side=tk.RIGHT)
        ttk.Button(btn_box, text="⚡ Run Duplicate Detection", style="Primary.TButton", command=self._trigger_run).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="🛡 Open Storage Optimizer", style="Secondary.TButton", command=self.on_navigate_to_optimizer).pack(side=tk.LEFT, padx=3)

        # Controls & Filter Bar
        ctrl_card = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=14, pady=10)
        ctrl_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(ctrl_card, text="Min Size:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        self.min_size_var = tk.StringVar(value="0")
        min_combo = ttk.Combobox(ctrl_card, textvariable=self.min_size_var, values=["0", "1 KB", "10 KB", "100 KB", "1 MB", "10 MB"], width=10, state="readonly")
        min_combo.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(ctrl_card, text="Category Filter:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        self.cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(
            ctrl_card,
            textvariable=self.cat_var,
            values=["All", "Document", "Image", "Code", "Archive", "Audio", "Video", "Other"],
            state="readonly",
            width=14,
        )
        cat_combo.pack(side=tk.LEFT, padx=(0, 20))

        self.byte_verify_var = tk.BooleanVar(value=True)
        chk_byte = ttk.Checkbutton(ctrl_card, text="Enable Stage 3 Byte Verification (100% collision proof)", variable=self.byte_verify_var)
        chk_byte.pack(side=tk.LEFT)

        # Progress bar
        self.progress_bar = ttk.Progressbar(ctrl_card, mode="determinate", length=180)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.lbl_progress = tk.Label(ctrl_card, text="Ready", font=FONTS["caption"], bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_progress.pack(side=tk.RIGHT, padx=5)

        # Summary Banner
        self.banner = tk.Frame(self, bg=COLORS["bg_card_secondary"], padx=14, pady=10, highlightbackground=COLORS["border_light"], highlightthickness=1)
        self.banner.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_summary_groups = tk.Label(self.banner, text="Duplicate Groups: 0", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"], fg=COLORS["primary"])
        self.lbl_summary_groups.pack(side=tk.LEFT, padx=(0, 25))

        self.lbl_summary_redundant = tk.Label(self.banner, text="Redundant File Copies: 0", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"], fg=COLORS["warning"])
        self.lbl_summary_redundant.pack(side=tk.LEFT, padx=(0, 25))

        self.lbl_summary_reclaimable = tk.Label(self.banner, text="Reclaimable Storage: 0 B", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"], fg=COLORS["success"])
        self.lbl_summary_reclaimable.pack(side=tk.LEFT, padx=(0, 25))

        # Master-Detail Paned Window
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # TOP PANE: Duplicate Groups
        top_frame = tk.Frame(paned, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        paned.add(top_frame, weight=2)

        tk.Label(top_frame, text="Identified Duplicate Groups (Click group to view all copies)", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"], padx=10, pady=4).pack(fill=tk.X)

        cols_g = ("group_id", "copies", "file_size", "reclaimable", "hash_short", "created_at")
        self.groups_table = ttk.Treeview(top_frame, columns=cols_g, show="headings", selectmode="browse")

        self.groups_table.heading("group_id", text="Group #")
        self.groups_table.heading("copies", text="File Copies (k)")
        self.groups_table.heading("file_size", text="File Size (S)")
        self.groups_table.heading("reclaimable", text="Reclaimable (k - 1) × S")
        self.groups_table.heading("hash_short", text="SHA-256 Digest")
        self.groups_table.heading("created_at", text="Discovered At")

        self.groups_table.column("group_id", width=70, anchor="center")
        self.groups_table.column("copies", width=120, anchor="center")
        self.groups_table.column("file_size", width=110, anchor="e")
        self.groups_table.column("reclaimable", width=160, anchor="e")
        self.groups_table.column("hash_short", width=220, anchor="center")
        self.groups_table.column("created_at", width=150, anchor="center")

        scroll_g = ttk.Scrollbar(top_frame, orient="vertical", command=self.groups_table.yview)
        self.groups_table.configure(yscrollcommand=scroll_g.set)
        self.groups_table.bind("<<TreeviewSelect>>", self._on_group_selected)

        self.groups_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_g.pack(side=tk.RIGHT, fill=tk.Y)

        # BOTTOM PANE: Constituent Files in Selected Group
        bot_frame = tk.Frame(paned, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        paned.add(bot_frame, weight=3)

        bot_header = tk.Frame(bot_frame, bg=COLORS["bg_card_secondary"], padx=10, pady=4)
        bot_header.pack(fill=tk.X)
        self.lbl_group_detail = tk.Label(bot_header, text="Group Details: Select a group above", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"])
        self.lbl_group_detail.pack(side=tk.LEFT)

        ttk.Button(bot_header, text="📂 Open File", style="Secondary.TButton", command=self._open_selected_file).pack(side=tk.RIGHT, padx=3)
        ttk.Button(bot_header, text="📁 Containing Folder", style="Secondary.TButton", command=self._open_containing_folder).pack(side=tk.RIGHT, padx=3)

        cols_f = ("role", "filename", "extension", "size", "modified_at", "path")
        self.files_table = ttk.Treeview(bot_frame, columns=cols_f, show="headings", selectmode="browse")

        self.files_table.heading("role", text="Role / Status")
        self.files_table.heading("filename", text="Filename")
        self.files_table.heading("extension", text="Ext")
        self.files_table.heading("size", text="Size")
        self.files_table.heading("modified_at", text="Modified Date")
        self.files_table.heading("path", text="Absolute Path")

        self.files_table.column("role", width=130, anchor="center")
        self.files_table.column("filename", width=200, anchor="w")
        self.files_table.column("extension", width=60, anchor="w")
        self.files_table.column("size", width=90, anchor="e")
        self.files_table.column("modified_at", width=140, anchor="center")
        self.files_table.column("path", width=340, anchor="w")

        scroll_f = ttk.Scrollbar(bot_frame, orient="vertical", command=self.files_table.yview)
        self.files_table.configure(yscrollcommand=scroll_f.set)
        self.files_table.bind("<Double-1>", lambda e: self._open_selected_file())

        self.files_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_f.pack(side=tk.RIGHT, fill=tk.Y)

    def _trigger_run(self) -> None:
        """Parse arguments and call runner."""
        val = self.min_size_var.get()
        size_map = {
            "0": 0,
            "1 KB": 1024,
            "10 KB": 10240,
            "100 KB": 102400,
            "1 MB": 1048576,
            "10 MB": 10485760,
        }
        min_bytes = size_map.get(val, 0)
        cat = self.cat_var.get()
        verify_bytes = self.byte_verify_var.get()

        self.on_run_detection(min_bytes, cat if cat != "All" else None, verify_bytes)

    def set_progress(self, stage_text: str, current: int, total: int) -> None:
        """Update progress bar from worker thread."""
        self.lbl_progress.config(text=f"{stage_text} ({current}/{total})")
        if total > 0:
            pct = (current / total) * 100
            self.progress_bar["value"] = pct

    def refresh_display(self) -> None:
        """Reload duplicate groups from database."""
        self.groups_data = self.get_duplicate_groups()

        # Update summary banner
        total_groups = len(self.groups_data)
        total_redundant = sum(g["file_count"] - 1 for g in self.groups_data)
        total_reclaimable = sum(g["reclaimable_size"] for g in self.groups_data)

        self.lbl_summary_groups.config(text=f"Duplicate Groups: {total_groups:,}")
        self.lbl_summary_redundant.config(text=f"Redundant Copies: {total_redundant:,}")
        self.lbl_summary_reclaimable.config(text=f"Reclaimable Storage: {format_bytes(total_reclaimable)}")

        # Clear and populate groups table
        for item in self.groups_table.get_children():
            self.groups_table.delete(item)

        for g in self.groups_data:
            hash_snippet = g["group_hash"][:16] + "..." if g["group_hash"] else "—"
            c_date = (g.get("created_at") or "")[:19].replace("T", " ")
            self.groups_table.insert(
                "",
                tk.END,
                values=(
                    g["group_id"],
                    f"{g['file_count']} copies",
                    format_bytes(g["file_size"]),
                    format_bytes(g["reclaimable_size"]),
                    hash_snippet,
                    c_date,
                ),
            )

        # Clear files table
        for item in self.files_table.get_children():
            self.files_table.delete(item)
        self.lbl_group_detail.config(text="Group Details: Select a group above")

    def _on_group_selected(self, event) -> None:
        """Populate files inside selected duplicate group."""
        sel = self.groups_table.selection()
        if not sel:
            return

        values = self.groups_table.item(sel[0], "values")
        group_id = int(values[0])

        group = next((g for g in self.groups_data if g["group_id"] == group_id), None)
        if not group:
            return

        self.lbl_group_detail.config(
            text=f"Group #{group_id} (Graph DFS Component) • SHA-256: {group['group_hash']} • {group['file_count']} identical copies"
        )

        for item in self.files_table.get_children():
            self.files_table.delete(item)

        for f in group["files"]:
            role = "👑 CANONICAL MASTER" if f.get("is_canonical") else "🗑 Redundant Copy"
            mod_str = (f.get("modified_at") or "")[:19].replace("T", " ")
            self.files_table.insert(
                "",
                tk.END,
                values=(
                    role,
                    f["filename"],
                    f.get("extension", ""),
                    format_bytes(group["file_size"]),
                    mod_str,
                    f["path"],
                ),
            )

    def _open_selected_file(self) -> None:
        sel = self.files_table.selection()
        if not sel:
            messagebox.showinfo("Select File", "Please select a file from the group details table.")
            return
        row = self.files_table.item(sel[0], "values")
        filepath = row[5]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found on disk:\n{filepath}")
            return
        try:
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file:\n{e}")

    def _open_containing_folder(self) -> None:
        sel = self.files_table.selection()
        if not sel:
            messagebox.showinfo("Select File", "Please select a file from the group details table.")
            return
        row = self.files_table.item(sel[0], "values")
        filepath = row[5]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found on disk:\n{filepath}")
            return
        try:
            subprocess.run(["explorer", f"/select,{os.path.normpath(filepath)}"], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")
