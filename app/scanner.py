"""
Recursive Directory Scanner with Tree Construction, SQLite Persistence,
and Incremental Indexing Support.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set, Any
from datetime import datetime

from app.config import (
    DEFAULT_EXCLUDED_NAMES,
    DEFAULT_EXCLUDED_EXTENSIONS,
    get_file_category,
)
from app.tree_structure import DirectoryTree, TreeNode
from app.database import DatabaseManager


class ScanCancelledException(Exception):
    """Raised when scan is cancelled by user."""
    pass


class DirectoryScanner:
    """
    Scans filesystem recursively, builds DirectoryTree, and synchronizes with SQLite.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        excluded_names: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None,
    ):
        self.db = db_manager
        self.excluded_names: Set[str] = set(excluded_names or DEFAULT_EXCLUDED_NAMES)
        self.excluded_extensions: Set[str] = set(excluded_extensions or DEFAULT_EXCLUDED_EXTENSIONS)
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Signal running scan to abort gracefully."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check if scan cancellation was requested."""
        return self._cancel_event.is_set()

    def scan_directory(
        self,
        root_path: str,
        incremental: bool = False,
        progress_callback: Optional[Callable[[int, int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Recursively scan root directory.
        
        Args:
            root_path: Root folder path
            incremental: If True, reuse existing records with matching size/mtime
            progress_callback: Callback(files_count, folders_count, total_bytes, current_path)
            
        Returns:
            Dictionary with scan statistics, tree, and elapsed time.
        """
        self._cancel_event.clear()
        norm_root = os.path.normpath(root_path)

        if not os.path.isdir(norm_root):
            raise FileNotFoundError(f"Selected root directory does not exist: {norm_root}")

        scan_id = self.db.record_scan_start(norm_root)
        start_time = time.perf_counter()

        # Existing files in DB for incremental comparison
        existing_db_files: Dict[str, Dict[str, Any]] = {}
        if incremental:
            for rec in self.db.get_all_files():
                existing_db_files[os.path.normpath(rec["path"])] = rec

        tree = DirectoryTree(norm_root)
        scanned_files_count = 0
        scanned_folders_count = 0
        scanned_bytes = 0
        error_count = 0
        errors: List[str] = []

        discovered_paths: Set[str] = set()
        staged_folders: List[Dict[str, Any]] = []
        staged_files: List[Dict[str, Any]] = []

        # Queue / Stack for iterative traversal (avoid recursion limits on deep trees)
        folder_queue = [norm_root]
        tree_node_map: Dict[str, TreeNode] = {norm_root: tree.root}

        try:
            while folder_queue:
                if self.is_cancelled():
                    raise ScanCancelledException("Scan cancelled by user.")

                current_dir = folder_queue.pop(0)
                current_node = tree_node_map.get(current_dir)
                scanned_folders_count += 1

                staged_folders.append({
                    "name": os.path.basename(current_dir) or current_dir,
                    "path": current_dir,
                    "parent_path": os.path.dirname(current_dir) if current_dir != norm_root else None,
                })

                try:
                    with os.scandir(current_dir) as entries:
                        for entry in entries:
                            if self.is_cancelled():
                                raise ScanCancelledException("Scan cancelled by user.")

                            name = entry.name
                            if name in self.excluded_names:
                                continue

                            entry_path = os.path.normpath(entry.path)

                            # Handle directories (strictly do not follow symlinks)
                            try:
                                is_symlink = entry.is_symlink()
                            except OSError:
                                is_symlink = False

                            if is_symlink:
                                continue

                            try:
                                if entry.is_dir(follow_symlinks=False):
                                    folder_queue.append(entry_path)
                                    child_dir_node = TreeNode(
                                        name=name,
                                        path=entry_path,
                                        is_directory=True,
                                        size=0,
                                        parent=current_node,
                                    )
                                    if current_node:
                                        current_node.add_child(child_dir_node)
                                    tree_node_map[entry_path] = child_dir_node

                                elif entry.is_file(follow_symlinks=False):
                                    ext = os.path.splitext(name)[1].lower()
                                    if ext in self.excluded_extensions:
                                        continue

                                    try:
                                        stat_info = entry.stat(follow_symlinks=False)
                                        file_size = stat_info.st_size
                                        mtime = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                                        try:
                                            ctime = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                                        except Exception:
                                            ctime = mtime
                                    except (PermissionError, OSError) as e:
                                        error_count += 1
                                        errors.append(f"Stat error on {entry_path}: {e}")
                                        continue

                                    scanned_files_count += 1
                                    scanned_bytes += file_size
                                    discovered_paths.add(entry_path)

                                    category = get_file_category(ext)
                                    content_hash = None
                                    hash_status = "PENDING"

                                    # Incremental logic: if file exists in DB and unmodified, preserve hash
                                    if incremental and entry_path in existing_db_files:
                                        old_rec = existing_db_files[entry_path]
                                        if old_rec["size"] == file_size and old_rec["modified_at"] == mtime:
                                            content_hash = old_rec.get("content_hash")
                                            hash_status = old_rec.get("hash_status", "PENDING")

                                    staged_files.append({
                                        "filename": name,
                                        "path": entry_path,
                                        "type": category,
                                        "extension": ext,
                                        "size": file_size,
                                        "created_at": ctime,
                                        "modified_at": mtime,
                                        "content_hash": content_hash,
                                        "hash_status": hash_status,
                                    })

                                    # Tree node
                                    child_file_node = TreeNode(
                                        name=name,
                                        path=entry_path,
                                        is_directory=False,
                                        size=file_size,
                                        parent=current_node,
                                        metadata={
                                            "extension": ext,
                                            "type": category,
                                            "modified_at": mtime,
                                        },
                                    )
                                    if current_node:
                                        current_node.add_child(child_file_node)

                                    if progress_callback and (scanned_files_count % 50 == 0):
                                        progress_callback(
                                            scanned_files_count,
                                            scanned_folders_count,
                                            scanned_bytes,
                                            entry_path,
                                        )

                            except (PermissionError, OSError) as e:
                                error_count += 1
                                errors.append(f"Access error for {entry_path}: {e}")

                except (PermissionError, OSError) as e:
                    error_count += 1
                    errors.append(f"Cannot read directory {current_dir}: {e}")

            # Reconcile deleted files in incremental mode
            deleted_count = 0
            if incremental:
                deleted_count = self.db.delete_files_not_in_paths(norm_root, discovered_paths)

            # Persist folders to SQLite
            path_to_folder_id = self.db.batch_insert_folders(staged_folders)

            # Attach parent_id to files
            for f in staged_files:
                parent_dir = os.path.dirname(f["path"])
                f["parent_id"] = path_to_folder_id.get(parent_dir)

            # Persist files to SQLite
            self.db.batch_upsert_files(staged_files)

            # Final progress update
            if progress_callback:
                progress_callback(scanned_files_count, scanned_folders_count, scanned_bytes, "Scan Complete")

            elapsed = time.perf_counter() - start_time
            self.db.record_scan_completion(
                scan_id=scan_id,
                files_scanned=scanned_files_count,
                folders_scanned=scanned_folders_count,
                bytes_scanned=scanned_bytes,
                status="COMPLETED",
                error_count=error_count,
            )

            return {
                "scan_id": scan_id,
                "status": "COMPLETED",
                "root_path": norm_root,
                "files_count": scanned_files_count,
                "folders_count": scanned_folders_count,
                "total_bytes": scanned_bytes,
                "elapsed_seconds": elapsed,
                "error_count": error_count,
                "errors": errors,
                "deleted_count": deleted_count,
                "tree": tree,
            }

        except ScanCancelledException:
            elapsed = time.perf_counter() - start_time
            self.db.record_scan_completion(
                scan_id=scan_id,
                files_scanned=scanned_files_count,
                folders_scanned=scanned_folders_count,
                bytes_scanned=scanned_bytes,
                status="CANCELLED",
                error_count=error_count,
            )
            return {
                "scan_id": scan_id,
                "status": "CANCELLED",
                "root_path": norm_root,
                "files_count": scanned_files_count,
                "folders_count": scanned_folders_count,
                "total_bytes": scanned_bytes,
                "elapsed_seconds": elapsed,
                "error_count": error_count,
                "errors": errors,
                "tree": tree,
            }
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self.db.record_scan_completion(
                scan_id=scan_id,
                files_scanned=scanned_files_count,
                folders_scanned=scanned_folders_count,
                bytes_scanned=scanned_bytes,
                status="FAILED",
                error_count=error_count + 1,
            )
            raise
