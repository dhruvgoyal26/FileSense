"""
Dashboard / Overview Screen for FileSense.
Displays real-time index metrics, storage distribution charts,
recent scans, and quick workflow triggers.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional, List
from app.config import format_bytes
from ui.styles import COLORS, FONTS


class DashboardView(ttk.Frame):
    """
    Overview Dashboard displaying live system statistics and visualizations.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_select_folder: Callable[[], None],
        on_start_scan: Callable[[], None],
        on_find_duplicates: Callable[[], None],
        on_search_files: Callable[[], None],
        on_generate_demo: Callable[[], None],
        on_refresh: Callable[[], None],
        on_add_folder: Optional[Callable[[], None]] = None,
        on_toggle_root: Optional[Callable[[int, bool], None]] = None,
        on_select_all_roots: Optional[Callable[[bool], None]] = None,
        on_remove_root: Optional[Callable[[int], None]] = None,
        on_scan_selected: Optional[Callable[[], None]] = None,
        on_apply_selection: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_select_folder = on_select_folder
        self.on_start_scan = on_start_scan
        self.on_find_duplicates = on_find_duplicates
        self.on_search_files = on_search_files
        self.on_generate_demo = on_generate_demo
        self.on_refresh = on_refresh
        self.on_add_folder = on_add_folder
        self.on_toggle_root = on_toggle_root
        self.on_select_all_roots = on_select_all_roots
        self.on_remove_root = on_remove_root
        self.on_scan_selected = on_scan_selected
        self.on_apply_selection = on_apply_selection

        self._build_ui()

    def _build_ui(self) -> None:
        # Header banner
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=25, pady=(20, 10))

        title_box = ttk.Frame(header_frame)
        title_box.pack(side=tk.LEFT)

        ttk.Label(
            title_box,
            text="System Overview & Storage Intelligence",
            font=FONTS["title_xl"],
        ).pack(anchor="w")

        ttk.Label(
            title_box,
            text="High-performance tree-indexed file analysis, SHA-256 redundancy verification, and DSA analytics.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(2, 0))

        # Quick Actions Bar
        actions_bar = ttk.Frame(header_frame)
        actions_bar.pack(side=tk.RIGHT)

        ttk.Button(
            actions_bar,
            text="📁 Select Folder",
            style="Primary.TButton",
            command=self.on_select_folder,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            actions_bar,
            text="⚡ Start Scan",
            style="Success.TButton",
            command=self.on_start_scan,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            actions_bar,
            text="🔍 Find Duplicates",
            style="Secondary.TButton",
            command=self.on_find_duplicates,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            actions_bar,
            text="🧪 Generate Demo Data",
            style="Secondary.TButton",
            command=self.on_generate_demo,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            actions_bar,
            text="🔄 Refresh",
            style="Secondary.TButton",
            command=self.on_refresh,
        ).pack(side=tk.LEFT, padx=4)

        # Scrollable container for dashboard content
        self.canvas = tk.Canvas(self, bg=COLORS["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))

        # 0. Active Workspace & Folder Selection Manager
        self._build_workspace_manager()

        # 1. Metric Cards Grid
        self._build_metric_cards()

        # 2. Charts and Distribution Section
        self._build_visualizations()

        # 3. Recent Activity / Scan History Table
        self._build_recent_activity_table()

    def _build_workspace_manager(self) -> None:
        """Create Workspace / Folder Scope selection card."""
        self.workspace_card = tk.Frame(
            self.scroll_frame,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        self.workspace_card.pack(fill=tk.X, padx=8, pady=(5, 12))

        # Top row: Title, Scope badge, Action buttons
        top_row = tk.Frame(self.workspace_card, bg=COLORS["bg_card"])
        top_row.pack(fill=tk.X, pady=(0, 8))

        left_title = tk.Frame(top_row, bg=COLORS["bg_card"])
        left_title.pack(side=tk.LEFT)

        tk.Label(
            left_title,
            text="📁 Selected Folders Workspace",
            font=FONTS["title_medium"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_workspace_summary = tk.Label(
            left_title,
            text="Workspace: [No folders selected]",
            font=FONTS["body_bold"],
            fg=COLORS["primary"],
            bg=COLORS["bg_card_secondary"],
            padx=8,
            pady=3,
            relief="solid",
            borderwidth=1,
        )
        self.lbl_workspace_summary.pack(side=tk.LEFT)

        # Right control buttons
        btn_box = tk.Frame(top_row, bg=COLORS["bg_card"])
        btn_box.pack(side=tk.RIGHT)

        ttk.Button(
            btn_box,
            text="➕ Add Folder",
            style="Primary.TButton",
            command=self.on_add_folder or self.on_select_folder,
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_box,
            text="☑️ Select All",
            style="Secondary.TButton",
            command=lambda: self._handle_select_all(True),
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_box,
            text="◻️ Clear All",
            style="Secondary.TButton",
            command=lambda: self._handle_select_all(False),
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_box,
            text="⚡ Scan Selected",
            style="Success.TButton",
            command=self.on_scan_selected or self.on_start_scan,
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_box,
            text="🔄 Apply Selection",
            style="Secondary.TButton",
            command=self.on_apply_selection or self.on_refresh,
        ).pack(side=tk.LEFT, padx=3)

        # Roots Treeview table
        tree_frame = tk.Frame(self.workspace_card, bg=COLORS["bg_card"])
        tree_frame.pack(fill=tk.X, expand=True, pady=(2, 6))

        cols = ("selected", "name", "path", "files", "size", "last_scanned", "status")
        self.roots_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=4, selectmode="browse")

        self.roots_tree.heading("selected", text="Active")
        self.roots_tree.heading("name", text="Folder Name")
        self.roots_tree.heading("path", text="Directory Path")
        self.roots_tree.heading("files", text="Files")
        self.roots_tree.heading("size", text="Total Size")
        self.roots_tree.heading("last_scanned", text="Last Scanned")
        self.roots_tree.heading("status", text="Status")

        self.roots_tree.column("selected", width=55, anchor="center")
        self.roots_tree.column("name", width=140, anchor="w")
        self.roots_tree.column("path", width=360, anchor="w")
        self.roots_tree.column("files", width=70, anchor="e")
        self.roots_tree.column("size", width=85, anchor="e")
        self.roots_tree.column("last_scanned", width=130, anchor="center")
        self.roots_tree.column("status", width=85, anchor="center")

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.roots_tree.yview)
        self.roots_tree.configure(yscrollcommand=tree_scroll_y.set)

        self.roots_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.roots_tree.bind("<Button-1>", self._on_roots_tree_click)
        self.roots_tree.bind("<Double-1>", self._on_roots_tree_double_click)

        # Bottom row: remove button and instructions
        bottom_row = tk.Frame(self.workspace_card, bg=COLORS["bg_card"])
        bottom_row.pack(fill=tk.X, pady=(4, 0))

        tk.Label(
            bottom_row,
            text="💡 Click any row to toggle its workspace selection. Check/uncheck folders to instantly scope dashboard & algorithms.",
            font=FONTS["caption"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
        ).pack(side=tk.LEFT)

        ttk.Button(
            bottom_row,
            text="🗑️ Remove Folder",
            style="Danger.TButton",
            command=self._handle_remove_root,
        ).pack(side=tk.RIGHT)

        # Empty selection warning banner (hidden when folders are selected)
        self.empty_banner = tk.Frame(
            self.scroll_frame,
            bg=COLORS["warning_light"],
            highlightbackground=COLORS["warning"],
            highlightthickness=1,
            padx=16,
            pady=10,
        )
        self.lbl_empty_banner = tk.Label(
            self.empty_banner,
            text="⚠️ Select at least one folder to view workspace data.",
            font=FONTS["body_bold"],
            fg="#92400e",
            bg=COLORS["warning_light"],
        )
        self.lbl_empty_banner.pack(anchor="w")

    def _on_roots_tree_click(self, event) -> None:
        """Handle click on tree row or checkbox to toggle is_selected."""
        region = self.roots_tree.identify_region(event.x, event.y)
        if region in ("tree", "cell"):
            item_id = self.roots_tree.identify_row(event.y)
            if item_id:
                self._toggle_item_selection(item_id)

    def _on_roots_tree_double_click(self, event) -> None:
        """Double click toggles selection."""
        item_id = self.roots_tree.identify_row(event.y)
        if item_id:
            self._toggle_item_selection(item_id)

    def _toggle_item_selection(self, item_id: str) -> None:
        values = self.roots_tree.item(item_id, "values")
        if not values or not self.on_toggle_root:
            return
        tags = self.roots_tree.item(item_id, "tags")
        if tags and len(tags) > 0:
            try:
                root_id = int(tags[0])
                current_sel = values[0]
                new_state = (current_sel != "☑")
                self.on_toggle_root(root_id, new_state)
            except ValueError:
                pass

    def _handle_select_all(self, select: bool) -> None:
        if self.on_select_all_roots:
            self.on_select_all_roots(select)

    def _handle_remove_root(self) -> None:
        sel = self.roots_tree.selection()
        if not sel:
            messagebox.showinfo("Selection Required", "Please select a folder row from the workspace table to remove.")
            return
        tags = self.roots_tree.item(sel[0], "tags")
        values = self.roots_tree.item(sel[0], "values")
        if tags and self.on_remove_root:
            try:
                root_id = int(tags[0])
                path_str = values[2] if len(values) > 2 else "this folder"
                confirm = messagebox.askyesno(
                    "Remove Workspace Folder",
                    f"Remove folder '{path_str}' from workspace configuration?\n\n(Existing files on disk will NOT be deleted).",
                )
                if confirm:
                    self.on_remove_root(root_id)
            except ValueError:
                pass

    def update_workspace_roots(self, roots_summary: List[Dict[str, Any]], summary_text: Optional[str] = None) -> None:
        """Populate the workspace roots table and update summary badge."""
        if summary_text is None:
            sel_roots = [r for r in roots_summary if r.get("is_selected", 1)]
            if not sel_roots:
                summary_text = "Workspace: None selected | 0 folders"
            else:
                names = [r.get("display_name") or os.path.basename(r["path"]) or r["path"] for r in sel_roots]
                if len(names) <= 2:
                    summary_text = f"Workspace: {' + '.join(names)} | {len(names)} selected"
                else:
                    summary_text = f"Workspace: {names[0]} + {names[1]} + {len(names) - 2} more | {len(names)} selected"

        self.lbl_workspace_summary.config(text=summary_text)

        for item in self.roots_tree.get_children():
            self.roots_tree.delete(item)

        selected_count = 0
        for r in roots_summary:
            is_sel = bool(r.get("is_selected", 1))
            if is_sel:
                selected_count += 1
            check_mark = "☑" if is_sel else "☐"
            name = r.get("display_name") or os.path.basename(r["path"]) or r["path"]
            f_count = r.get("file_count", 0)
            f_size = format_bytes(r.get("total_size", 0))
            last_scanned = (r.get("last_scanned_at") or "Not scanned")[:19].replace("T", " ")
            status = r.get("scan_status") or "PENDING"

            self.roots_tree.insert(
                "",
                tk.END,
                values=(
                    check_mark,
                    name,
                    r["path"],
                    f"{f_count:,}",
                    f_size,
                    last_scanned,
                    status,
                ),
                tags=(str(r["id"]),),
            )

        if selected_count == 0:
            self.empty_banner.pack(fill=tk.X, padx=8, pady=(0, 10), before=self.cards_frame)
        else:
            self.empty_banner.pack_forget()

    def _build_metric_cards(self) -> None:
        """Create responsive stat cards."""
        self.cards_frame = ttk.Frame(self.scroll_frame)
        self.cards_frame.pack(fill=tk.X, padx=5, pady=(10, 15))

        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1, uniform="stat_card")

        # Card 1: Indexed Files
        self.card_files, self.lbl_files = self._create_card(
            self.cards_frame, 0, 0, "Indexed Files", "0", "0 folders discovered", "#2563eb"
        )
        # Card 2: Total Size
        self.card_size, self.lbl_size = self._create_card(
            self.cards_frame, 0, 1, "Total Storage Indexed", "0 B", "Across all monitored trees", "#4f46e5"
        )
        # Card 3: Duplicate Groups
        self.card_dups, self.lbl_dups = self._create_card(
            self.cards_frame, 0, 2, "Duplicate Groups", "0", "0 redundant copies found", "#f59e0b"
        )
        # Card 4: Reclaimable Storage
        self.card_reclaim, self.lbl_reclaim = self._create_card(
            self.cards_frame, 0, 3, "Potential Storage Savings", "0 B", "Formula: ∑ (k - 1) × S", "#10b981"
        )

    def _create_card(
        self,
        parent: ttk.Frame,
        row: int,
        col: int,
        title: str,
        value: str,
        subtitle: str,
        accent_color: str,
    ) -> tuple[tk.Frame, tk.Label]:
        card = tk.Frame(
            parent,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")

        # Top indicator line
        top_bar = tk.Frame(card, bg=accent_color, height=3)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        lbl_title = tk.Label(
            card,
            text=title,
            font=FONTS["body_bold"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_card"],
        )
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(
            card,
            text=value,
            font=FONTS["stat_number"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        )
        lbl_val.pack(anchor="w", pady=(4, 2))

        lbl_sub = tk.Label(
            card,
            text=subtitle,
            font=FONTS["caption"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
        )
        lbl_sub.pack(anchor="w")

        return card, lbl_val

    def _build_visualizations(self) -> None:
        """Create split section with Extension Bar Chart and Category Breakdown."""
        charts_row = ttk.Frame(self.scroll_frame)
        charts_row.pack(fill=tk.X, padx=5, pady=10)
        charts_row.columnconfigure(0, weight=3)
        charts_row.columnconfigure(1, weight=2)

        # Left: Storage by File Extension (Canvas Bar Chart)
        chart_card = tk.Frame(
            charts_row,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        chart_card.grid(row=0, column=0, padx=8, sticky="nsew")

        tk.Label(
            chart_card,
            text="Storage Consumption by File Extension",
            font=FONTS["title_medium"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w")

        tk.Label(
            chart_card,
            text="Top file formats occupying disk storage in indexed trees",
            font=FONTS["caption"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", pady=(0, 8))

        self.bar_canvas = tk.Canvas(chart_card, bg="#ffffff", height=180, highlightthickness=0)
        self.bar_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        # Right: Category Distribution Card
        cat_card = tk.Frame(
            charts_row,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        cat_card.grid(row=0, column=1, padx=8, sticky="nsew")

        tk.Label(
            cat_card,
            text="File Category Breakdown",
            font=FONTS["title_medium"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w")

        tk.Label(
            cat_card,
            text="Distribution of files by functional type",
            font=FONTS["caption"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", pady=(0, 8))

        self.cat_list_frame = tk.Frame(cat_card, bg=COLORS["bg_card"])
        self.cat_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def _build_recent_activity_table(self) -> None:
        """Create recent scan history table on dashboard."""
        table_card = tk.Frame(
            self.scroll_frame,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        table_card.pack(fill=tk.X, padx=13, pady=(10, 20))

        tk.Label(
            table_card,
            text="Recent Indexing & Scan Activity",
            font=FONTS["title_medium"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w")

        tk.Label(
            table_card,
            text="Audit log of filesystem traversals recorded in SQLite database",
            font=FONTS["caption"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", pady=(0, 10))

        cols = ("id", "root_path", "started_at", "files", "folders", "bytes", "status", "errors")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=5)

        self.tree.heading("id", text="#")
        self.tree.heading("root_path", text="Scanned Root Path")
        self.tree.heading("started_at", text="Timestamp")
        self.tree.heading("files", text="Files")
        self.tree.heading("folders", text="Folders")
        self.tree.heading("bytes", text="Size")
        self.tree.heading("status", text="Status")
        self.tree.heading("errors", text="Errors")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("root_path", width=300, anchor="w")
        self.tree.column("started_at", width=140, anchor="center")
        self.tree.column("files", width=70, anchor="e")
        self.tree.column("folders", width=70, anchor="e")
        self.tree.column("bytes", width=90, anchor="e")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("errors", width=60, anchor="center")

        self.tree.pack(fill=tk.X, expand=True)

    def update_metrics(self, summary_data: Dict[str, Any], scan_history: List[Dict[str, Any]]) -> None:
        """Update dashboard with fresh data."""
        total_files = summary_data.get("total_files", 0)
        total_size = summary_data.get("total_size", 0)
        total_folders = summary_data.get("total_folders", 0)
        dup_groups = summary_data.get("duplicate_groups", 0)
        redundant_copies = summary_data.get("redundant_copies", 0)
        reclaimable_bytes = summary_data.get("reclaimable_size", 0)

        # Update card labels
        self.lbl_files.config(text=f"{total_files:,}")
        self.lbl_size.config(text=format_bytes(total_size))
        self.lbl_dups.config(text=f"{dup_groups:,}")
        self.lbl_reclaim.config(text=format_bytes(reclaimable_bytes))

        # Update Extension Bar Chart
        self._render_bar_chart(summary_data.get("extension_stats", []))

        # Update Category Breakdown
        self._render_category_list(summary_data.get("category_stats", []))

        # Update Recent Scan Activity Table
        for row in self.tree.get_children():
            self.tree.delete(row)

        for s in scan_history[:8]:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    s.get("id"),
                    s.get("root_path"),
                    (s.get("started_at") or "")[:19].replace("T", " "),
                    f"{s.get('files_scanned', 0):,}",
                    f"{s.get('folders_scanned', 0):,}",
                    format_bytes(s.get("bytes_scanned", 0)),
                    s.get("status"),
                    s.get("error_count", 0),
                ),
            )

    def _render_bar_chart(self, extension_stats: List[Dict[str, Any]]) -> None:
        """Draw responsive horizontal bar chart on Canvas."""
        self.bar_canvas.delete("all")
        w = self.bar_canvas.winfo_width() or 450
        h = self.bar_canvas.winfo_height() or 180

        if not extension_stats:
            self.bar_canvas.create_text(
                w / 2,
                h / 2,
                text="No files indexed in selected workspace. Check folders above or click 'Add Folder'.",
                fill=COLORS["text_muted"],
                font=FONTS["body"],
            )
            return

        max_size = max((item["total_size"] for item in extension_stats), default=1)
        max_size = max(1, max_size)

        bar_colors = ["#2563eb", "#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#64748b"]

        num_items = min(len(extension_stats), 6)
        row_h = (h - 20) / max(1, num_items)

        for i in range(num_items):
            item = extension_stats[i]
            ext = item["extension"] or "[None]"
            size = item["total_size"]
            count = item["count"]
            color = bar_colors[i % len(bar_colors)]

            y = 10 + i * row_h
            bar_w = ((w - 180) * size) / max_size
            bar_w = max(4, bar_w)

            # Label (Extension)
            self.bar_canvas.create_text(
                10,
                y + row_h / 2,
                anchor="w",
                text=ext.upper(),
                font=FONTS["body_bold"],
                fill=COLORS["text_primary"],
            )

            # Bar
            self.bar_canvas.create_rectangle(
                70,
                y + 3,
                70 + bar_w,
                y + row_h - 5,
                fill=color,
                outline="",
            )

            # Value label
            self.bar_canvas.create_text(
                75 + bar_w + 5,
                y + row_h / 2,
                anchor="w",
                text=f"{format_bytes(size)} ({count} files)",
                font=FONTS["caption"],
                fill=COLORS["text_secondary"],
            )

    def _render_category_list(self, category_stats: List[Dict[str, Any]]) -> None:
        """Render category list with progress bars."""
        for child in self.cat_list_frame.winfo_children():
            child.destroy()

        if not category_stats:
            tk.Label(
                self.cat_list_frame,
                text="No files indexed in selected workspace",
                font=FONTS["body_small"],
                fg=COLORS["text_muted"],
                bg=COLORS["bg_card"],
            ).pack(anchor="w", pady=10)
            return

        total_files = sum(c["count"] for c in category_stats) or 1

        for c in category_stats[:5]:
            cat_name = c["type"]
            count = c["count"]
            pct = (count / total_files) * 100

            row = tk.Frame(self.cat_list_frame, bg=COLORS["bg_card"])
            row.pack(fill=tk.X, pady=4)

            lbl_frame = tk.Frame(row, bg=COLORS["bg_card"])
            lbl_frame.pack(fill=tk.X)

            tk.Label(
                lbl_frame,
                text=cat_name,
                font=FONTS["body_bold"],
                fg=COLORS["text_primary"],
                bg=COLORS["bg_card"],
            ).pack(side=tk.LEFT)

            tk.Label(
                lbl_frame,
                text=f"{count} files ({pct:.1f}%)",
                font=FONTS["caption"],
                fg=COLORS["text_secondary"],
                bg=COLORS["bg_card"],
            ).pack(side=tk.RIGHT)

            # Progress bar simulation
            bar_bg = tk.Frame(row, bg="#e2e8f0", height=6)
            bar_bg.pack(fill=tk.X, pady=(2, 0))

            fill_width = max(0.01, min(1.0, count / total_files))
            bar_fill = tk.Frame(bar_bg, bg=COLORS["primary"], height=6)
            bar_fill.place(relx=0, rely=0, relwidth=fill_width, relheight=1)
