"""
File Explorer and Index Screen.
Provides interactive folder tree hierarchy navigation,
file table with sorting, filtering, and OS shell launch integration.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
from app.config import format_bytes
from ui.styles import COLORS, FONTS


class FileExplorerView(ttk.Frame):
    """
    Split-pane File Explorer with Directory Folder Tree on left
    and searchable, sortable file table on right.
    """

    def __init__(
        self,
        parent: tk.Widget,
        get_all_files: Callable[[], List[Dict[str, Any]]],
        get_all_folders: Callable[[], List[Dict[str, Any]]],
        duplicate_ids_provider: Callable[[], set[int]],
    ):
        super().__init__(parent)
        self.get_all_files = get_all_files
        self.get_all_folders = get_all_folders
        self.duplicate_ids_provider = duplicate_ids_provider

        self.current_files: List[Dict[str, Any]] = []
        self.selected_folder_path: Optional[str] = None
        self.sort_column = "filename"
        self.sort_descending = False

        self._build_ui()

    def _build_ui(self) -> None:
        # Top Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(toolbar)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="File Explorer & Persistent Index", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Hierarchical directory tree with instant table filtering and file operations",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Action Buttons on Right
        btn_box = ttk.Frame(toolbar)
        btn_box.pack(side=tk.RIGHT)

        ttk.Button(btn_box, text="📂 Open File", style="Secondary.TButton", command=self._open_selected_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="📁 Containing Folder", style="Secondary.TButton", command=self._open_containing_folder).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="📋 Copy Path", style="Secondary.TButton", command=self._copy_selected_path).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_box, text="🔄 Refresh Table", style="Secondary.TButton", command=self.refresh_data).pack(side=tk.LEFT, padx=3)

        # Filter Sub-bar
        filter_bar = tk.Frame(self, bg=COLORS["bg_card"], padx=12, pady=8, highlightbackground=COLORS["border_light"], highlightthickness=1)
        filter_bar.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(filter_bar, text="Filter:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._apply_filters())
        entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=30)
        entry.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(filter_bar, text="Category:", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        self.cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(
            filter_bar,
            textvariable=self.cat_var,
            values=["All", "Document", "Image", "Code", "Archive", "Audio", "Video", "Other"],
            state="readonly",
            width=14,
        )
        cat_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        cat_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Show all button
        ttk.Button(filter_bar, text="Show All Folders", style="Secondary.TButton", command=self._clear_folder_selection).pack(side=tk.LEFT)

        # Status text on right
        self.lbl_stats = tk.Label(filter_bar, text="0 files | 0 B", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"])
        self.lbl_stats.pack(side=tk.RIGHT)

        # Main Paned Window (Split into Tree on left, Table on right)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # LEFT PANE: Folder Hierarchy Tree
        left_frame = tk.Frame(paned, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        paned.add(left_frame, weight=1)

        tree_header = tk.Frame(left_frame, bg=COLORS["bg_card_secondary"], padx=10, pady=6)
        tree_header.pack(fill=tk.X)
        tk.Label(tree_header, text="Folder Hierarchy", font=FONTS["body_bold"], bg=COLORS["bg_card_secondary"], fg=COLORS["text_primary"]).pack(side=tk.LEFT)

        self.folder_tree = ttk.Treeview(left_frame, selectmode="browse", show="tree")
        folder_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=folder_scroll.set)
        self.folder_tree.bind("<<TreeviewSelect>>", self._on_folder_selected)

        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        folder_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # RIGHT PANE: File List Table
        right_frame = tk.Frame(paned, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        paned.add(right_frame, weight=3)

        cols = ("filename", "extension", "size", "type", "modified_at", "duplicate", "path")
        self.file_table = ttk.Treeview(right_frame, columns=cols, show="headings", selectmode="extended")

        col_widths = {
            "filename": 220,
            "extension": 70,
            "size": 90,
            "type": 90,
            "modified_at": 140,
            "duplicate": 90,
            "path": 300,
        }

        col_titles = {
            "filename": "Filename",
            "extension": "Ext",
            "size": "Size",
            "type": "Type",
            "modified_at": "Modified Date",
            "duplicate": "Duplicate?",
            "path": "Full Location Path",
        }

        for c in cols:
            self.file_table.heading(c, text=col_titles[c], command=lambda col=c: self._sort_by(col))
            self.file_table.column(c, width=col_widths[c], anchor="w" if c not in ("size", "duplicate") else "e")

        self.file_table.column("duplicate", anchor="center")

        table_scroll_y = ttk.Scrollbar(right_frame, orient="vertical", command=self.file_table.yview)
        table_scroll_x = ttk.Scrollbar(right_frame, orient="horizontal", command=self.file_table.xview)
        self.file_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)

        self.file_table.bind("<Double-1>", lambda e: self._open_selected_file())

        self.file_table.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        table_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        table_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_data(self) -> None:
        """Reload folders and files from data providers."""
        self._populate_folder_tree()
        self.current_files = self.get_all_files()
        self._apply_filters()

    def _populate_folder_tree(self) -> None:
        """Build folder tree nodes from database folders."""
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)

        folders = self.get_all_folders()
        if not folders:
            return

        # Sort folders by path depth
        sorted_folders = sorted(folders, key=lambda f: f["path"].count(os.sep))
        node_map = {}

        for f in sorted_folders:
            path = os.path.normpath(f["path"])
            name = f["name"]
            parent_dir = os.path.dirname(path)

            parent_id = node_map.get(parent_dir, "")
            node_id = self.folder_tree.insert(parent_id, "end", text=f"📁 {name}", values=(path,))
            node_map[path] = node_id

        # Expand root nodes
        for root_item in self.folder_tree.get_children():
            self.folder_tree.item(root_item, open=True)

    def _on_folder_selected(self, event) -> None:
        """Filter table to selected folder."""
        sel = self.folder_tree.selection()
        if not sel:
            self.selected_folder_path = None
        else:
            values = self.folder_tree.item(sel[0], "values")
            if values:
                self.selected_folder_path = values[0]
        self._apply_filters()

    def _clear_folder_selection(self) -> None:
        """Clear tree selection to show all files."""
        self.folder_tree.selection_remove(self.folder_tree.selection())
        self.selected_folder_path = None
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Filter and sort current file set, updating table."""
        query = self.search_var.get().strip().lower()
        cat = self.cat_var.get()
        dup_ids = self.duplicate_ids_provider()

        filtered: List[Dict[str, Any]] = []
        norm_folder = os.path.normpath(self.selected_folder_path) if self.selected_folder_path else None

        for f in self.current_files:
            # Folder subtree filter
            if norm_folder:
                fpath = os.path.normpath(f["path"])
                if not (fpath == norm_folder or fpath.startswith(norm_folder + os.sep)):
                    continue

            # Query filter
            if query and (query not in f["filename"].lower() and query not in f["path"].lower()):
                continue

            # Category filter
            if cat != "All" and f.get("type") != cat:
                continue

            f_copy = dict(f)
            f_copy["is_dup"] = f["id"] in dup_ids
            filtered.append(f_copy)

        # Sort
        filtered = self._sort_records(filtered)

        # Update Treeview rows
        for item in self.file_table.get_children():
            self.file_table.delete(item)

        total_size = sum(f["size"] for f in filtered)
        self.lbl_stats.config(text=f"{len(filtered):,} files  |  {format_bytes(total_size)}")

        for f in filtered:
            dup_label = "⚠️ Duplicate" if f["is_dup"] else "—"
            mod_str = (f.get("modified_at") or "")[:19].replace("T", " ")
            self.file_table.insert(
                "",
                tk.END,
                values=(
                    f["filename"],
                    f.get("extension", ""),
                    format_bytes(f["size"]),
                    f.get("type", "Other"),
                    mod_str,
                    dup_label,
                    f["path"],
                ),
            )

    def _sort_by(self, col: str) -> None:
        """Toggle column sort order."""
        if self.sort_column == col:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col
            self.sort_descending = False
        self._apply_filters()

    def _sort_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort records list by selected column."""
        col = self.sort_column
        rev = self.sort_descending

        if col == "size":
            return sorted(records, key=lambda x: x.get("size", 0), reverse=rev)
        elif col == "modified_at":
            return sorted(records, key=lambda x: x.get("modified_at") or "", reverse=rev)
        elif col == "duplicate":
            return sorted(records, key=lambda x: x.get("is_dup", False), reverse=rev)
        elif col == "extension":
            return sorted(records, key=lambda x: (x.get("extension") or "").lower(), reverse=rev)
        elif col == "path":
            return sorted(records, key=lambda x: x.get("path", "").lower(), reverse=rev)
        else:
            return sorted(records, key=lambda x: x.get("filename", "").lower(), reverse=rev)

    def _get_selected_row(self) -> Optional[tuple]:
        sel = self.file_table.selection()
        if not sel:
            messagebox.showinfo("Selection Required", "Please select a file from the table.")
            return None
        return self.file_table.item(sel[0], "values")

    def _open_selected_file(self) -> None:
        """Launch selected file with OS default program."""
        row = self._get_selected_row()
        if not row:
            return
        filepath = row[6]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found on disk:\n{filepath}")
            return
        try:
            os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Cannot Open File", f"Error opening file:\n{e}")

    def _open_containing_folder(self) -> None:
        """Open Windows Explorer with file selected."""
        row = self._get_selected_row()
        if not row:
            return
        filepath = row[6]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found on disk:\n{filepath}")
            return
        try:
            subprocess.run(["explorer", f"/select,{os.path.normpath(filepath)}"], check=False)
        except Exception as e:
            messagebox.showerror("Cannot Open Folder", f"Error opening folder:\n{e}")

    def _copy_selected_path(self) -> None:
        """Copy file path to clipboard."""
        row = self._get_selected_row()
        if not row:
            return
        filepath = row[6]
        self.clipboard_clear()
        self.clipboard_append(filepath)
        messagebox.showinfo("Copied", f"File path copied to clipboard:\n{filepath}")
