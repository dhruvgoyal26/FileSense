"""
Scan History and Audit Log Screen for FileSense.
Displays historical index runs persisted in SQLite database.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Callable
from app.config import format_bytes
from ui.styles import COLORS, FONTS


class HistoryView(ttk.Frame):
    """
    Scan History view showing chronological audit logs of filesystem scans.
    """

    def __init__(self, parent: tk.Widget, get_scan_history: Callable[[], List[Dict[str, Any]]]):
        super().__init__(parent)
        self.get_scan_history = get_scan_history
        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        title_box = ttk.Frame(header)
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="Persistent Scan History & Audit Logs", font=FONTS["title_large"]).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Chronological record of directory scans, indexed byte volumes, and scan outcomes.",
            font=FONTS["body_small"],
            foreground=COLORS["text_secondary"],
        ).pack(anchor="w")

        btn_box = ttk.Frame(header)
        btn_box.pack(side=tk.RIGHT)
        ttk.Button(btn_box, text="🔄 Refresh History", style="Secondary.TButton", command=self.refresh_data).pack(side=tk.LEFT)

        # Table Card
        table_frame = tk.Frame(self, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        cols = ("id", "root_path", "started_at", "completed_at", "files", "folders", "bytes", "status", "errors")
        self.history_table = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.history_table.heading("id", text="#")
        self.history_table.heading("root_path", text="Scanned Root Path")
        self.history_table.heading("started_at", text="Started At")
        self.history_table.heading("completed_at", text="Completed At")
        self.history_table.heading("files", text="Files Scanned")
        self.history_table.heading("folders", text="Folders")
        self.history_table.heading("bytes", text="Data Volume")
        self.history_table.heading("status", text="Outcome Status")
        self.history_table.heading("errors", text="Errors")

        self.history_table.column("id", width=50, anchor="center")
        self.history_table.column("root_path", width=300, anchor="w")
        self.history_table.column("started_at", width=140, anchor="center")
        self.history_table.column("completed_at", width=140, anchor="center")
        self.history_table.column("files", width=90, anchor="e")
        self.history_table.column("folders", width=80, anchor="e")
        self.history_table.column("bytes", width=100, anchor="e")
        self.history_table.column("status", width=100, anchor="center")
        self.history_table.column("errors", width=70, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=scroll_y.set)

        self.history_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_data(self) -> None:
        """Fetch scan history from database."""
        for item in self.history_table.get_children():
            self.history_table.delete(item)

        history = self.get_scan_history()
        for s in history:
            start_str = (s.get("started_at") or "")[:19].replace("T", " ")
            end_str = (s.get("completed_at") or "")[:19].replace("T", " ") if s.get("completed_at") else "—"

            self.history_table.insert(
                "",
                tk.END,
                values=(
                    s.get("id"),
                    s.get("root_path"),
                    start_str,
                    end_str,
                    f"{s.get('files_scanned', 0):,}",
                    f"{s.get('folders_scanned', 0):,}",
                    format_bytes(s.get("bytes_scanned", 0)),
                    s.get("status"),
                    s.get("error_count", 0),
                ),
            )
