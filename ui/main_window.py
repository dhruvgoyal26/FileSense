"""
Main Application Window for FileSense.
Coordinates persistent dark navy sidebar navigation, background worker threads,
view switching, and live synchronization across database and in-memory indexes.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional, Any

from app.config import APP_NAME, APP_VERSION, DEFAULT_DB_PATH
from app.database import DatabaseManager
from app.file_index import FileIndex
from app.scanner import DirectoryScanner
from app.duplicate_detector import DuplicateDetector
from app.storage_optimizer import StorageOptimizer
from scripts.generate_demo_data import generate_demo_dataset

from ui.styles import apply_theme, COLORS, FONTS
from ui.dashboard import DashboardView
from ui.file_explorer import FileExplorerView
from ui.search_view import SearchView
from ui.duplicates_view import DuplicatesView
from ui.optimizer_view import OptimizerView
from ui.history_view import HistoryView


class MainWindow(tk.Tk):
    """
    Root Tkinter window orchestrating the FileSense desktop interface.
    """

    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(1150, 720)

        # Initialize Backend Subsystems
        self.db = DatabaseManager(db_path or DEFAULT_DB_PATH)
        self.file_index = FileIndex()
        self.scanner = DirectoryScanner(self.db)
        self.detector = DuplicateDetector(self.db)
        self.optimizer = StorageOptimizer(self.db)

        # State tracking
        self.current_root_path: Optional[str] = None
        self.is_scanning = False
        self.is_detecting = False
        self.nav_buttons: Dict[str, tk.Label] = {}
        self.active_nav = "Dashboard"

        # Apply Modern Styling
        self.style = apply_theme(self)

        # Build Layout
        self._build_main_layout()

        # Load Initial Data from SQLite into In-Memory Index
        self.reload_from_database()

    def _build_main_layout(self) -> None:
        """Construct Persistent Sidebar, Header, Content Area, and Status Bar."""
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Left Sidebar
        self.sidebar_frame = tk.Frame(self.main_container, bg=COLORS["sidebar_bg"], width=240)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        self._build_sidebar()

        # 2. Right Workspace Area
        self.workspace_frame = ttk.Frame(self.main_container)
        self.workspace_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header Bar
        self._build_header_bar()

        # Dynamic View Container (where screens are swapped)
        self.content_frame = ttk.Frame(self.workspace_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Instantiate View Frames
        self.views: Dict[str, ttk.Frame] = {}

        self.views["Dashboard"] = DashboardView(
            self.content_frame,
            on_select_folder=self.add_workspace_folder_dialog,
            on_start_scan=self.start_scan_workspace_thread,
            on_find_duplicates=lambda: self.switch_view("Duplicate Detection"),
            on_search_files=lambda: self.switch_view("Search Files"),
            on_generate_demo=self.generate_demo_and_scan,
            on_refresh=self.reload_from_database,
            on_add_folder=self.add_workspace_folder_dialog,
            on_toggle_root=self.toggle_workspace_root,
            on_select_all_roots=self.select_all_workspace_roots,
            on_remove_root=self.remove_workspace_root,
            on_scan_selected=self.start_scan_workspace_thread,
            on_apply_selection=self.reload_from_database,
        )

        self.views["File Explorer / File Index"] = FileExplorerView(
            self.content_frame,
            get_all_files=lambda: self.db.get_files_for_roots(self.db.get_selected_root_paths()),
            get_all_folders=lambda: self.db.get_folders_for_roots(self.db.get_selected_root_paths()),
            duplicate_ids_provider=lambda: self.file_index.duplicate_file_ids,
        )

        self.views["Search Files"] = SearchView(
            self.content_frame,
            file_index=self.file_index,
            get_current_root=self._get_active_benchmark_root,
        )

        self.views["Duplicate Detection"] = DuplicatesView(
            self.content_frame,
            on_run_detection=self.start_duplicate_detection_thread,
            get_duplicate_groups=lambda: self.db.get_duplicate_groups_with_files(root_paths=self.db.get_selected_root_paths()),
            on_navigate_to_optimizer=lambda: self.switch_view("Storage Optimizer"),
        )

        self.views["Storage Optimizer"] = OptimizerView(
            self.content_frame,
            optimizer=self.optimizer,
            on_refresh_data=self.reload_from_database,
            get_selected_roots=lambda: self.db.get_selected_root_paths(),
        )

        self.views["Scan History"] = HistoryView(
            self.content_frame,
            get_scan_history=self.db.get_scan_history,
        )

        for v in self.views.values():
            v.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Bottom Status Bar
        self._build_status_bar()

        # Show initial screen
        self.switch_view("Dashboard")

    def _build_sidebar(self) -> None:
        """Create dark navy sidebar with application branding and 9 navigation links."""
        # Brand logo and title
        brand_box = tk.Frame(self.sidebar_frame, bg=COLORS["sidebar_bg"], padx=18, pady=20)
        brand_box.pack(fill=tk.X)

        tk.Label(
            brand_box,
            text="⚡ FileSense",
            font=FONTS["title_large"],
            fg="#ffffff",
            bg=COLORS["sidebar_bg"],
        ).pack(anchor="w")

        tk.Label(
            brand_box,
            text="Local File Intelligence • CCSE0301",
            font=FONTS["caption"],
            fg=COLORS["sidebar_subtext"],
            bg=COLORS["sidebar_bg"],
        ).pack(anchor="w", pady=(2, 0))

        # Separator line
        tk.Frame(self.sidebar_frame, bg=COLORS["sidebar_border"], height=1).pack(fill=tk.X, padx=14, pady=(0, 10))

        # 6 Core Navigation Sections
        nav_items = [
            ("Dashboard", "📊 Dashboard"),
            ("File Explorer / File Index", "📁 File Explorer / File Index"),
            ("Search Files", "🔍 Search Files"),
            ("Duplicate Detection", "♊ Duplicate Detection"),
            ("Storage Optimizer", "🛡 Storage Optimizer"),
            ("Scan History", "⏱ Scan History"),
        ]

        nav_container = tk.Frame(self.sidebar_frame, bg=COLORS["sidebar_bg"])
        nav_container.pack(fill=tk.BOTH, expand=True, pady=8)

        for key, display_text in nav_items:
            btn = tk.Label(
                nav_container,
                text=f"  {display_text}",
                font=FONTS["body_bold"],
                fg=COLORS["sidebar_text"],
                bg=COLORS["sidebar_bg"],
                anchor="w",
                padx=16,
                pady=14,
                cursor="hand2",
            )
            btn.pack(fill=tk.X, padx=10, pady=4)
            btn.bind("<Button-1>", lambda e, k=key: self.switch_view(k))
            btn.bind("<Enter>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, True))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_nav_hover(b, k, False))
            self.nav_buttons[key] = btn

        # Footer info and About dialog launcher
        footer_box = tk.Frame(self.sidebar_frame, bg=COLORS["sidebar_bg"], padx=16, pady=16)
        footer_box.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(
            footer_box,
            text="DSA-II Final PBL Project",
            font=FONTS["caption"],
            fg=COLORS["sidebar_subtext"],
            bg=COLORS["sidebar_bg"],
        ).pack(anchor="w")

        tk.Label(
            footer_box,
            text="SDG 9: Industry & Innovation",
            font=FONTS["caption"],
            fg=COLORS["sidebar_subtext"],
            bg=COLORS["sidebar_bg"],
        ).pack(anchor="w", pady=(0, 8))

        btn_about = tk.Label(
            footer_box,
            text="ℹ About FileSense",
            font=FONTS["body_small"],
            fg=COLORS["sidebar_text"],
            bg=COLORS["sidebar_bg"],
            cursor="hand2",
        )
        btn_about.pack(anchor="w")
        btn_about.bind("<Button-1>", lambda e: self._show_about_dialog())
        btn_about.bind("<Enter>", lambda e: btn_about.configure(fg="#ffffff"))
        btn_about.bind("<Leave>", lambda e: btn_about.configure(fg=COLORS["sidebar_text"]))

    def _on_nav_hover(self, btn: tk.Label, key: str, is_hover: bool) -> None:
        if key == self.active_nav:
            return
        if is_hover:
            btn.configure(bg=COLORS["sidebar_hover"], fg="#ffffff")
        else:
            btn.configure(bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_text"])

    def switch_view(self, view_name: str) -> None:
        """Switch visible screen and highlight sidebar button."""
        if view_name not in self.views:
            return

        self.active_nav = view_name

        # Update sidebar button highlights
        for k, btn in self.nav_buttons.items():
            if k == view_name:
                btn.configure(bg=COLORS["primary"], fg="#ffffff")
            else:
                btn.configure(bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_text"])

        # Raise selected view
        target_view = self.views[view_name]
        target_view.tkraise()

        # Update header page title
        self.lbl_header_title.config(text=view_name)

        # Trigger on-show refresh if applicable
        if view_name == "Dashboard":
            selected_roots = self.db.get_selected_root_paths()
            summary = self.db.get_dashboard_summary(root_paths=selected_roots)
            history = self.db.get_scan_history(limit=8)
            roots_summary = self.db.get_workspace_roots_summary()
            target_view.update_metrics(summary, history)
            target_view.update_workspace_roots(roots_summary)
        elif view_name == "File Explorer / File Index":
            target_view.refresh_data()
        elif view_name == "Duplicate Detection":
            target_view.refresh_display()
        elif view_name == "Storage Optimizer":
            target_view.load_plan()
        elif view_name == "Scan History":
            target_view.refresh_data()
        elif view_name == "Search Files":
            target_view.execute_search()

    def _build_header_bar(self) -> None:
        """Top Header Bar with active workspace summary and scanner controls."""
        header_bar = tk.Frame(self.workspace_frame, bg="#ffffff", height=55, padx=20, highlightbackground=COLORS["border_light"], highlightthickness=1)
        header_bar.pack(fill=tk.X)
        header_bar.pack_propagate(False)

        # Left: Active Page Title
        self.lbl_header_title = tk.Label(header_bar, text="Dashboard", font=FONTS["title_medium"], bg="#ffffff", fg=COLORS["text_primary"])
        self.lbl_header_title.pack(side=tk.LEFT)

        # Center/Right: Current Selected Root & Quick Scan Action
        right_box = tk.Frame(header_bar, bg="#ffffff")
        right_box.pack(side=tk.RIGHT)

        tk.Label(right_box, text="Workspace:", font=FONTS["body_bold"], bg="#ffffff", fg=COLORS["text_secondary"]).pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_active_root = tk.Label(
            right_box,
            text="[No Folders Selected]",
            font=FONTS["mono"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
            padx=8,
            pady=3,
            relief="solid",
            borderwidth=1,
        )
        self.lbl_active_root.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_header_scan = ttk.Button(right_box, text="⚡ Scan Workspace", style="Primary.TButton", command=self.start_scan_workspace_thread)
        self.btn_header_scan.pack(side=tk.LEFT, padx=3)

        self.btn_header_cancel = ttk.Button(right_box, text="🛑 Cancel", style="Danger.TButton", state="disabled", command=self._cancel_active_task)
        self.btn_header_cancel.pack(side=tk.LEFT, padx=3)

    def _build_status_bar(self) -> None:
        """Bottom status bar with message and item counter."""
        self.status_bar = tk.Frame(self.workspace_frame, bg=COLORS["bg_card_secondary"], height=28, padx=15, highlightbackground=COLORS["border_light"], highlightthickness=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        self.lbl_status_msg = tk.Label(
            self.status_bar,
            text="Ready • SQLite index active",
            font=FONTS["caption"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_secondary"],
        )
        self.lbl_status_msg.pack(side=tk.LEFT)

        self.lbl_status_stats = tk.Label(
            self.status_bar,
            text="0 files indexed",
            font=FONTS["caption"],
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_secondary"],
        )
        self.lbl_status_stats.pack(side=tk.RIGHT)

    # ==========================================================
    # State Management & Background Threading
    # ==========================================================

    def reload_from_database(self) -> None:
        """Load SQLite records for selected roots into FileIndex and refresh UI."""
        selected_roots = self.db.get_selected_root_paths()
        records = self.db.get_files_for_roots(selected_roots)
        self.file_index.load_from_records(records)

        # Load duplicate file IDs for active roots
        dup_groups = self.db.get_duplicate_groups_with_files(root_paths=selected_roots)
        dup_ids = set()
        for g in dup_groups:
            for f in g.get("files", []):
                dup_ids.add(f["file_id"])
        self.file_index.set_duplicate_file_ids(dup_ids)

        # Update header active workspace label
        self._update_header_workspace_label()

        # Update dashboard
        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        history = self.db.get_scan_history(limit=8)
        roots_summary = self.db.get_workspace_roots_summary()
        self.views["Dashboard"].update_metrics(summary, history)
        self.views["Dashboard"].update_workspace_roots(roots_summary)

        self.lbl_status_stats.config(text=f"{len(records):,} files in workspace")
        if not selected_roots:
            self.lbl_status_msg.config(text="No folders selected in workspace • Select or add folders to analyze")
        else:
            self.lbl_status_msg.config(text=f"Workspace synchronized ({len(records):,} files, {len(dup_groups):,} duplicate groups across {len(selected_roots)} roots)")

    def _update_header_workspace_label(self) -> None:
        """Update top bar label with compact workspace root summary."""
        selected_roots = self.db.get_selected_root_paths()
        if not selected_roots:
            self.lbl_active_root.config(text="[No Folders Selected]", fg=COLORS["warning"])
            return

        names = []
        for r in selected_roots:
            base = os.path.basename(r.rstrip("\\/"))
            names.append(base if base else r)

        if len(names) == 1:
            text_val = f"{names[0]} (1 folder)"
        elif len(names) <= 3:
            text_val = f"{' + '.join(names)} ({len(names)} folders)"
        else:
            text_val = f"{names[0]} + {names[1]} + {len(names) - 2} more ({len(names)} folders)"

        self.lbl_active_root.config(text=text_val, fg=COLORS["text_primary"])

    def _get_active_benchmark_root(self) -> Optional[str]:
        """Return the first accessible selected root folder for raw filesystem benchmarks."""
        selected_roots = self.db.get_selected_root_paths()
        for r in selected_roots:
            if os.path.isdir(r):
                return r
        if self.current_root_path and os.path.isdir(self.current_root_path):
            return self.current_root_path
        return None

    def add_workspace_folder_dialog(self) -> None:
        """Open folder selection dialog and add folder to workspace."""
        folder = filedialog.askdirectory(title="Add Folder to Workspace")
        if folder:
            norm_folder = os.path.normpath(folder)
            self.current_root_path = norm_folder
            self.db.add_workspace_root(norm_folder, is_selected=True)
            self.reload_from_database()

            # Offer immediate scan
            should_scan = messagebox.askyesno(
                "Scan Folder Now?",
                f"Added '{os.path.basename(norm_folder)}' to your workspace.\n\n"
                f"Path: {norm_folder}\n\n"
                f"Would you like to scan and index this folder now?",
                parent=self,
            )
            if should_scan:
                self.start_scan_workspace_thread(root_paths=[norm_folder])

    def select_folder_dialog(self) -> None:
        """Alias for adding folder to workspace."""
        self.add_workspace_folder_dialog()

    def toggle_workspace_root(self, root_id: int, is_selected: bool) -> None:
        """Toggle inclusion of a root folder in current workspace."""
        self.db.set_workspace_root_selected(root_id, is_selected)
        self.reload_from_database()

    def select_all_workspace_roots(self, is_selected: bool) -> None:
        """Select or deselect all root folders in workspace."""
        self.db.set_all_workspace_roots_selected(is_selected)
        self.reload_from_database()

    def remove_workspace_root(self, root_id: int) -> None:
        """Remove a root folder from workspace tracking."""
        self.db.remove_workspace_root(root_id)
        self.reload_from_database()

    def start_scan_workspace_thread(self, root_paths: Optional[List[str]] = None) -> None:
        """Scan all selected workspace roots (or specified roots) in a background worker thread."""
        if root_paths is None:
            root_paths = self.db.get_selected_root_paths()

        if not root_paths:
            msg = messagebox.askyesno(
                "No Folders Selected",
                "Your workspace currently has no folders selected.\n\n"
                "Would you like to select/add a folder now?",
                parent=self,
            )
            if msg:
                self.add_workspace_folder_dialog()
            return

        if self.is_scanning:
            messagebox.showinfo("Scan Active", "A filesystem scan is already in progress.")
            return

        self.is_scanning = True
        self.btn_header_scan.configure(state="disabled")
        self.btn_header_cancel.configure(state="normal")

        def _worker():
            total_files = 0
            total_folders = 0
            total_bytes = 0
            total_errors = 0
            scanned_roots = 0
            cancelled = False

            for i, rpath in enumerate(root_paths, 1):
                if cancelled:
                    break
                if not os.path.exists(rpath):
                    self.db.update_workspace_root_scan_status(rpath, "Unavailable")
                    continue

                self.db.update_workspace_root_scan_status(rpath, "Scanning...")
                self.after(
                    0,
                    lambda p=rpath, idx=i, tot=len(root_paths): self.lbl_status_msg.config(
                        text=f"Scanning folder {idx}/{tot}: {os.path.basename(p)} ..."
                    ),
                )

                def _progress_cb(f_count, d_count, b_count, cur_path):
                    self.after(
                        0,
                        lambda fc=f_count, dc=d_count, cp=cur_path, idx=i, tot=len(root_paths): self.lbl_status_msg.config(
                            text=f"Folder {idx}/{tot} ({fc:,} files)... {os.path.basename(cp)}"
                        ),
                    )

                result = self.scanner.scan_directory(
                    root_path=rpath,
                    incremental=True,
                    progress_callback=_progress_cb,
                )

                if result["status"] == "CANCELLED":
                    self.db.update_workspace_root_scan_status(rpath, "Cancelled")
                    cancelled = True
                    break
                elif result["status"] == "COMPLETED":
                    self.db.update_workspace_root_scan_status(rpath, "Indexed")
                    total_files += result["files_count"]
                    total_folders += result["folders_count"]
                    total_bytes += result["total_bytes"]
                    total_errors += result["error_count"]
                    scanned_roots += 1
                else:
                    self.db.update_workspace_root_scan_status(rpath, "Failed")

            self.after(
                0,
                lambda: self._on_workspace_scan_completed(
                    cancelled, scanned_roots, len(root_paths), total_files, total_folders, total_bytes, total_errors
                ),
            )

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _on_workspace_scan_completed(
        self, cancelled: bool, scanned_count: int, total_count: int, files: int, folders: int, total_b: int, errors: int
    ) -> None:
        self.is_scanning = False
        self.btn_header_scan.configure(state="normal")
        self.btn_header_cancel.configure(state="disabled")

        self.reload_from_database()

        if cancelled:
            self.lbl_status_msg.config(text="Workspace scan was cancelled by user.")
        else:
            messagebox.showinfo(
                "Workspace Scan Finished",
                f"Finished scanning selected workspace folders!\n\n"
                f"Folders Scanned: {scanned_count} of {total_count}\n"
                f"Total Files Indexed: {files:,}\n"
                f"Total Subdirectories: {folders:,}\n"
                f"Total Size: {total_b:,} bytes\n"
                f"Errors Encountered: {errors}\n\n"
                f"Current workspace view and indexes have been refreshed.",
            )

    def start_scan_thread(self) -> None:
        """Scan workspace folders."""
        self.start_scan_workspace_thread()

    def start_duplicate_detection_thread(self, min_size: int, cat: Optional[str], verify_bytes: bool) -> None:
        """Run duplicate detection in background worker thread scoped to active workspace roots."""
        if self.is_detecting:
            messagebox.showinfo("Task Active", "Duplicate detection is already running.")
            return

        selected_roots = self.db.get_selected_root_paths()
        if not selected_roots:
            messagebox.showwarning(
                "No Workspace Folders",
                "No folders are currently selected in your workspace.\n\n"
                "Please select or add at least one folder on the Dashboard to detect duplicates.",
            )
            return

        self.is_detecting = True
        self.btn_header_cancel.configure(state="normal")

        dup_view: DuplicatesView = self.views["Duplicate Detection"]

        def _worker():
            try:
                def _prog(stage, curr, tot):
                    self.after(0, lambda: dup_view.set_progress(stage, curr, tot))

                result = self.detector.detect_duplicates(
                    min_size=min_size,
                    type_filter=cat,
                    verify_bytes=verify_bytes,
                    progress_callback=_prog,
                    root_paths=selected_roots,
                )
                self.after(0, lambda: self._on_detection_completed(result))
            except Exception as e:
                self.after(0, lambda: self._on_detection_failed(str(e)))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _on_detection_completed(self, result: Dict[str, Any]) -> None:
        self.is_detecting = False
        self.btn_header_cancel.configure(state="disabled")

        if result.get("status") == "COMPLETED":
            self.reload_from_database()
            dup_view: DuplicatesView = self.views["Duplicate Detection"]
            dup_view.refresh_display()

            messagebox.showinfo(
                "Duplicate Detection Complete",
                f"Multi-stage duplicate detection finished!\n\n"
                f"Groups Discovered: {result['total_groups']}\n"
                f"Redundant Copies: {result['total_redundant_copies']}\n"
                f"Total Reclaimable Storage: {result['total_reclaimable_bytes']:,} bytes\n\n"
                f"Review the identified duplicate groups or navigate\n"
                f"to 'Storage Optimizer' to plan safe cleanup.",
            )
        elif result.get("status") == "CANCELLED":
            self.lbl_status_msg.config(text="Duplicate detection cancelled.")

    def _on_detection_failed(self, error_msg: str) -> None:
        self.is_detecting = False
        self.btn_header_cancel.configure(state="disabled")
        messagebox.showerror("Detection Error", f"Error during duplicate detection:\n{error_msg}")

    def _cancel_active_task(self) -> None:
        """Cancel running scan or duplicate detection."""
        if self.is_scanning:
            self.scanner.cancel()
            self.lbl_status_msg.config(text="Cancelling directory scan...")
        if self.is_detecting:
            self.detector.cancel()
            self.lbl_status_msg.config(text="Cancelling duplicate detection...")

    def generate_demo_and_scan(self) -> None:
        """Generate demo dataset, register in workspace roots, and start scan automatically."""
        try:
            demo_dir = generate_demo_dataset()
            norm_demo = os.path.normpath(demo_dir)
            self.current_root_path = norm_demo
            self.db.add_workspace_root(norm_demo, is_selected=True)
            self.reload_from_database()
            self.start_scan_workspace_thread([norm_demo])
        except Exception as e:
            messagebox.showerror("Demo Generation Error", f"Failed to generate demo data:\n{e}")

    def clear_database_and_reload(self) -> None:
        """Wipe database records and clear index."""
        self.db.clear_database()
        self.file_index.clear()
        self.reload_from_database()

    def _show_about_dialog(self) -> None:
        """Display academic project details, DSA architecture, and index maintenance in a clean modal dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(f"About {APP_NAME}")
        dialog.geometry("620x540")
        dialog.minsize(560, 480)
        dialog.transient(self)
        dialog.grab_set()

        # Canvas & scrollable container
        canvas = tk.Canvas(dialog, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_win = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 0), pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15, padx=(0, 15))

        # Header Box
        header = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header, text=f"⚡ {APP_NAME} v{APP_VERSION}", font=FONTS["title_large"], bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w")
        tk.Label(header, text="High-Performance Local File Indexing and Redundancy Detection Tool", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(2, 0))
        tk.Label(
            header,
            text="Data Structures & Algorithms-II (CCSE0301) Individual PBL Submission\nUN Sustainable Development Goal 9: Industry, Innovation, and Infrastructure",
            font=FONTS["caption"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # DSA Architecture
        dsa_card = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        dsa_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(dsa_card, text="Data Structures & Algorithms Architecture", font=FONTS["title_medium"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))

        dsa_text = (
            "• Tree Structure: N-ary DirectoryTree modeling folder/file hierarchies with recursive size aggregation.\n"
            "• Hash Tables: Python in-memory dictionaries providing O(1) avg lookups by name, path, extension, and hash.\n"
            "• Duplicate Detection: Multi-stage pipeline (Size pre-filter -> SHA-256 chunk streaming -> Byte verification).\n"
            "• Graph Algorithms: Internal Adjacency List representing duplicate equivalence; DFS traversal identifies connected duplicate clusters.\n"
            "• Dynamic Programming: 0/1 Knapsack optimization maximizes storage reclamation within a defined budget.\n"
            "• SQLite Persistence: ACID storage in WAL mode for incremental scans and historical audit logs."
        )
        tk.Label(dsa_card, text=dsa_text, justify="left", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")

        # System Config
        sys_card = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        sys_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(sys_card, text="System & Database Parameters", font=FONTS["title_medium"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))
        cfg_text = (
            f"• Database Path: {self.db.db_path}\n"
            f"• SQLite Mode: Write-Ahead Logging (WAL), Foreign Keys ON\n"
            f"• Safety Guarantee: Non-destructive recommendations; master copies are always protected."
        )
        tk.Label(sys_card, text=cfg_text, justify="left", font=FONTS["mono"], bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(anchor="w")

        # Database Maintenance
        db_card = tk.Frame(scroll_frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border_light"], highlightthickness=1, padx=16, pady=14)
        db_card.pack(fill=tk.X, pady=(0, 15))

        tk.Label(db_card, text="Database Maintenance", font=FONTS["title_medium"], bg=COLORS["bg_card"], fg=COLORS["danger"]).pack(anchor="w", pady=(0, 4))
        tk.Label(
            db_card,
            text="Wipe all persistent indexing records, duplicate groups, and scan logs from SQLite.\n(Does not delete any files from your disk).",
            font=FONTS["caption"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"],
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        btn_row = ttk.Frame(db_card)
        btn_row.pack(fill=tk.X)

        def _on_wipe():
            confirm = messagebox.askyesno(
                "Confirm Database Reset",
                "Are you sure you want to clear all indexed files, folders, and duplicate groups from SQLite?\n\nThis will not delete any files on your disk.",
                parent=dialog,
                icon="warning",
            )
            if confirm:
                self.clear_database_and_reload()
                messagebox.showinfo("Database Cleared", "The database index has been completely reset.", parent=dialog)
                dialog.destroy()

        ttk.Button(btn_row, text="⚠️ Reset Database Index", style="Danger.TButton", command=_on_wipe).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Close", style="Secondary.TButton", command=dialog.destroy).pack(side=tk.RIGHT)
