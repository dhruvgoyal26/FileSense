"""
SQLite Persistence Layer for FileSense.
Stores file and folder metadata, hashes, scan logs, and duplicate groups.
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Iterator
from datetime import datetime
from contextlib import contextmanager
from app.config import DEFAULT_DB_PATH


def is_path_under_roots(path: str, norm_roots: List[str]) -> bool:
    """
    Check if a path equals or resides within any of the normalized root directories.
    Uses os.path.normcase and os.path.normpath for robust Windows/Unix case-insensitive matching.
    """
    if not norm_roots:
        return False
    norm_p = os.path.normcase(os.path.normpath(os.path.abspath(path)))
    for r in norm_roots:
        norm_r = os.path.normcase(os.path.normpath(os.path.abspath(r)))
        if norm_p == norm_r or norm_p.startswith(norm_r + os.sep):
            return True
    return False


class DatabaseManager:
    """
    Manages SQLite database operations with WAL mode, parameterized queries,
    and foreign key constraints.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Context manager for atomic transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Create required tables and indexes if they do not exist."""
        with self.transaction() as cur:
            # 1. Folders table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    indexed_at TEXT NOT NULL
                );
            """)

            # 2. Files table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    filename TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_at TEXT,
                    modified_at TEXT,
                    content_hash TEXT,
                    hash_status TEXT DEFAULT 'PENDING',
                    indexed_at TEXT NOT NULL,
                    FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE SET NULL
                );
            """)

            # 3. Scan history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_path TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    files_scanned INTEGER DEFAULT 0,
                    folders_scanned INTEGER DEFAULT 0,
                    bytes_scanned INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    error_count INTEGER DEFAULT 0
                );
            """)

            # 4. Duplicate groups table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_hash TEXT UNIQUE NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_count INTEGER NOT NULL,
                    reclaimable_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 5. Duplicate group files junction table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_group_files (
                    group_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    is_canonical INTEGER DEFAULT 0,
                    PRIMARY KEY (group_id, file_id),
                    FOREIGN KEY (group_id) REFERENCES duplicate_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                );
            """)

            # 6. Workspace Roots table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workspace_roots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    is_selected INTEGER DEFAULT 1,
                    last_scanned_at TEXT,
                    scan_status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL
                );
            """)

            # Performance Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_workspace_roots_path ON workspace_roots(path);")

    # ==========================================
    # Workspace Roots operations
    # ==========================================

    def add_workspace_root(
        self,
        path: str,
        display_name: Optional[str] = None,
        is_selected: bool = True,
    ) -> Dict[str, Any]:
        """Add or update a workspace root folder."""
        norm_path = os.path.normpath(os.path.abspath(path))
        name = display_name or os.path.basename(norm_path) or norm_path
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO workspace_roots (path, display_name, is_selected, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    display_name = excluded.display_name,
                    is_selected = excluded.is_selected;
            """, (norm_path, name, 1 if is_selected else 0, now))
            cur.execute("SELECT * FROM workspace_roots WHERE path = ?;", (norm_path,))
            return dict(cur.fetchone())

    def get_workspace_roots(self) -> List[Dict[str, Any]]:
        """Retrieve all configured workspace root folders."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM workspace_roots ORDER BY path ASC;")
            rows = [dict(r) for r in cur.fetchall()]
            if not rows:
                # If table empty, attempt to seed from scan_history if available
                cur.execute("SELECT DISTINCT root_path FROM scan_history ORDER BY id ASC;")
                history_roots = [r["root_path"] for r in cur.fetchall()]
                now = datetime.now().isoformat()
                for hr in history_roots:
                    norm_hr = os.path.normpath(hr)
                    if os.path.exists(norm_hr):
                        name = os.path.basename(norm_hr) or norm_hr
                        with self.transaction() as write_cur:
                            write_cur.execute("""
                                INSERT OR IGNORE INTO workspace_roots (path, display_name, is_selected, created_at)
                                VALUES (?, ?, 1, ?);
                            """, (norm_hr, name, now))
                cur.execute("SELECT * FROM workspace_roots ORDER BY path ASC;")
                rows = [dict(r) for r in cur.fetchall()]
            return rows
        finally:
            conn.close()

    def set_workspace_root_selected(self, root_id: Any, is_selected: bool) -> None:
        """Toggle selected state for a workspace root folder."""
        if isinstance(root_id, dict):
            root_id = root_id.get("id")
        with self.transaction() as cur:
            cur.execute(
                "UPDATE workspace_roots SET is_selected = ? WHERE id = ?;",
                (1 if is_selected else 0, root_id),
            )

    def set_all_workspace_roots_selected(self, is_selected: bool) -> None:
        """Select or deselect all workspace root folders."""
        with self.transaction() as cur:
            cur.execute(
                "UPDATE workspace_roots SET is_selected = ?;",
                (1 if is_selected else 0,),
            )

    def remove_workspace_root(self, root_id: Any) -> None:
        """Remove a root folder from workspace roots (does not delete indexed files)."""
        if isinstance(root_id, dict):
            root_id = root_id.get("id")
        with self.transaction() as cur:
            cur.execute("DELETE FROM workspace_roots WHERE id = ?;", (root_id,))

    def update_workspace_root_scan_status(
        self,
        path: str,
        status: str,
        scanned_at: Optional[str] = None,
    ) -> None:
        """Update last scan status and timestamp for a root folder."""
        norm_path = os.path.normpath(os.path.abspath(path))
        now = scanned_at or datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                UPDATE workspace_roots
                SET scan_status = ?, last_scanned_at = ?
                WHERE path = ?;
            """, (status, now, norm_path))

    def get_selected_root_paths(self) -> List[str]:
        """Return list of normalized paths for currently selected workspace roots."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT path FROM workspace_roots WHERE is_selected = 1 ORDER BY path ASC;")
            return [os.path.normpath(r["path"]) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_workspace_roots_summary(self) -> List[Dict[str, Any]]:
        """Return all workspace roots with live counts of indexed files and total sizes."""
        roots = self.get_workspace_roots()
        all_files = self.get_all_files()
        result = []
        for r in roots:
            r_path = os.path.normpath(r["path"])
            matching = [f for f in all_files if is_path_under_roots(f["path"], [r_path])]
            r_dict = dict(r)
            r_dict["file_count"] = len(matching)
            r_dict["total_size"] = sum(f["size"] for f in matching)
            result.append(r_dict)
        return result

    def get_files_for_roots(self, root_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Return files filtered to those under any of root_paths.
        Guarantees that each physical file is included at most once, even if parent and child roots are both selected.
        """
        if root_paths is None:
            return self.get_all_files()
        if not root_paths:
            return []
        norm_roots = [os.path.normpath(r) for r in root_paths]
        all_files = self.get_all_files()
        return [f for f in all_files if is_path_under_roots(f["path"], norm_roots)]

    def get_folders_for_roots(self, root_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return folders filtered to those under any of root_paths."""
        if root_paths is None:
            return self.get_all_folders()
        if not root_paths:
            return []
        norm_roots = [os.path.normpath(r) for r in root_paths]
        all_folders = self.get_all_folders()
        return [f for f in all_folders if is_path_under_roots(f["path"], norm_roots)]

    # ==========================================
    # Folder operations
    # ==========================================

    def upsert_folder(self, name: str, path: str, parent_id: Optional[int] = None) -> int:
        """Insert or update folder record, returning folder id."""
        norm_path = os.path.normpath(path)
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO folders (parent_id, name, path, indexed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    name = excluded.name,
                    parent_id = excluded.parent_id,
                    indexed_at = excluded.indexed_at;
            """, (parent_id, name, norm_path, now))
            cur.execute("SELECT id FROM folders WHERE path = ?", (norm_path,))
            row = cur.fetchone()
            return row["id"]

    def batch_insert_folders(self, folder_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Batch insert folders and return dict mapping norm_path -> folder_id.
        Each dict should contain: 'name', 'path', 'parent_path' (optional)
        """
        if not folder_list:
            return {}

        now = datetime.now().isoformat()
        path_to_id: Dict[str, int] = {}

        with self.transaction() as cur:
            for item in folder_list:
                norm_path = os.path.normpath(item["path"])
                name = item["name"]
                cur.execute("""
                    INSERT INTO folders (name, path, indexed_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        name = excluded.name,
                        indexed_at = excluded.indexed_at;
                """, (name, norm_path, now))

            # Populate mapping
            cur.execute("SELECT id, path FROM folders;")
            for row in cur.fetchall():
                path_to_id[row["path"]] = row["id"]

            # Update parent_ids if parent_path supplied
            for item in folder_list:
                parent_path = item.get("parent_path")
                if parent_path:
                    norm_parent = os.path.normpath(parent_path)
                    parent_id = path_to_id.get(norm_parent)
                    if parent_id:
                        norm_path = os.path.normpath(item["path"])
                        cur.execute("UPDATE folders SET parent_id = ? WHERE path = ?", (parent_id, norm_path))

        return path_to_id

    # ==========================================
    # File operations
    # ==========================================

    def upsert_file(self, file_data: Dict[str, Any]) -> int:
        """Insert or update single file record and return file id."""
        norm_path = os.path.normpath(file_data["path"])
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO files (
                    parent_id, filename, path, type, extension, size,
                    created_at, modified_at, content_hash, hash_status, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    parent_id = excluded.parent_id,
                    filename = excluded.filename,
                    type = excluded.type,
                    extension = excluded.extension,
                    size = excluded.size,
                    created_at = excluded.created_at,
                    modified_at = excluded.modified_at,
                    content_hash = excluded.content_hash,
                    hash_status = excluded.hash_status,
                    indexed_at = excluded.indexed_at;
            """, (
                file_data.get("parent_id"),
                file_data["filename"],
                norm_path,
                file_data["type"],
                file_data["extension"],
                file_data["size"],
                file_data.get("created_at"),
                file_data.get("modified_at"),
                file_data.get("content_hash"),
                file_data.get("hash_status", "PENDING"),
                now,
            ))
            cur.execute("SELECT id FROM files WHERE path = ?", (norm_path,))
            return cur.fetchone()["id"]

    def batch_upsert_files(self, file_list: List[Dict[str, Any]]) -> List[int]:
        """Batch upsert files efficiently within a single transaction."""
        if not file_list:
            return []

        now = datetime.now().isoformat()
        inserted_ids = []
        with self.transaction() as cur:
            for f in file_list:
                norm_path = os.path.normpath(f["path"])
                cur.execute("""
                    INSERT INTO files (
                        parent_id, filename, path, type, extension, size,
                        created_at, modified_at, content_hash, hash_status, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        parent_id = excluded.parent_id,
                        filename = excluded.filename,
                        type = excluded.type,
                        extension = excluded.extension,
                        size = excluded.size,
                        created_at = excluded.created_at,
                        modified_at = excluded.modified_at,
                        content_hash = CASE
                            WHEN excluded.content_hash IS NOT NULL THEN excluded.content_hash
                            ELSE files.content_hash
                        END,
                        hash_status = CASE
                            WHEN excluded.hash_status IS NOT NULL THEN excluded.hash_status
                            ELSE files.hash_status
                        END,
                        indexed_at = excluded.indexed_at;
                """, (
                    f.get("parent_id"),
                    f["filename"],
                    norm_path,
                    f["type"],
                    f["extension"],
                    f["size"],
                    f.get("created_at"),
                    f.get("modified_at"),
                    f.get("content_hash"),
                    f.get("hash_status", "PENDING"),
                    now,
                ))

            # Retrieve assigned IDs
            paths = [os.path.normpath(f["path"]) for f in file_list]
            for p in paths:
                cur.execute("SELECT id FROM files WHERE path = ?", (p,))
                row = cur.fetchone()
                if row:
                    inserted_ids.append(row["id"])

        return inserted_ids

    def update_file_hash(self, file_id: int, content_hash: Optional[str], hash_status: str) -> None:
        """Update hash and status for a file."""
        with self.transaction() as cur:
            cur.execute("""
                UPDATE files
                SET content_hash = ?, hash_status = ?
                WHERE id = ?;
            """, (content_hash, hash_status, file_id))

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Return all files as list of dicts."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM files ORDER BY filename ASC;")
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_all_folders(self) -> List[Dict[str, Any]]:
        """Return all folders."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM folders ORDER BY path ASC;")
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single file by ID."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_files_by_path_prefix(self, folder_path: str) -> List[Dict[str, Any]]:
        """Get all files located within a directory path prefix."""
        norm_path = os.path.normpath(folder_path)
        pattern = norm_path + os.sep + "%"
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM files
                WHERE path = ? OR path LIKE ?
                ORDER BY filename ASC;
            """, (norm_path, pattern))
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def delete_files_not_in_paths(self, root_path: str, valid_paths: set[str]) -> int:
        """Remove indexed files within root_path that no longer exist on disk."""
        norm_root = os.path.normpath(root_path)
        pattern = norm_root + os.sep + "%"
        conn = self.get_connection()
        deleted_count = 0
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, path FROM files WHERE path = ? OR path LIKE ?;", (norm_root, pattern))
            rows = cur.fetchall()
            ids_to_delete = [r["id"] for r in rows if r["path"] not in valid_paths]
            if ids_to_delete:
                placeholders = ",".join("?" for _ in ids_to_delete)
                cur.execute(f"DELETE FROM files WHERE id IN ({placeholders});", ids_to_delete)
                conn.commit()
                deleted_count = len(ids_to_delete)
            return deleted_count
        finally:
            conn.close()

    def clear_database(self) -> None:
        """Clear all records from files, folders, duplicates, history, and workspace roots."""
        with self.transaction() as cur:
            cur.execute("DELETE FROM duplicate_group_files;")
            cur.execute("DELETE FROM duplicate_groups;")
            cur.execute("DELETE FROM files;")
            cur.execute("DELETE FROM folders;")
            cur.execute("DELETE FROM scan_history;")
            cur.execute("DELETE FROM workspace_roots;")

    # ==========================================
    # Duplicate groups persistence
    # ==========================================

    def save_duplicate_groups(
        self,
        groups: List[Dict[str, Any]]
    ) -> None:
        """
        Save discovered duplicate groups and their constituent files.
        Each group: {
            'group_hash': str,
            'file_size': int,
            'file_count': int,
            'reclaimable_size': int,
            'files': [{'file_id': int, 'is_canonical': bool}, ...]
        }
        """
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            # Clear previous duplicate group links
            cur.execute("DELETE FROM duplicate_group_files;")
            cur.execute("DELETE FROM duplicate_groups;")

            for g in groups:
                cur.execute("""
                    INSERT INTO duplicate_groups (
                        group_hash, file_size, file_count, reclaimable_size, created_at
                    ) VALUES (?, ?, ?, ?, ?);
                """, (
                    g["group_hash"],
                    g["file_size"],
                    g["file_count"],
                    g["reclaimable_size"],
                    now,
                ))
                group_id = cur.lastrowid
                for f in g["files"]:
                    cur.execute("""
                        INSERT INTO duplicate_group_files (group_id, file_id, is_canonical)
                        VALUES (?, ?, ?);
                    """, (group_id, f["file_id"], 1 if f.get("is_canonical") else 0))

    def get_duplicate_groups_with_files(self, root_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all duplicate groups with full file details.
        If root_paths is provided, filters files to those within root_paths,
        and retains only groups with >= 2 matching files in the active workspace.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    dg.id AS group_id,
                    dg.group_hash,
                    dg.file_size,
                    dg.file_count,
                    dg.reclaimable_size,
                    dg.created_at AS group_created_at,
                    dgf.is_canonical,
                    f.id AS file_id,
                    f.filename,
                    f.path,
                    f.extension,
                    f.type,
                    f.modified_at,
                    f.content_hash,
                    f.hash_status
                FROM duplicate_groups dg
                JOIN duplicate_group_files dgf ON dg.id = dgf.group_id
                JOIN files f ON dgf.file_id = f.id
                ORDER BY dg.reclaimable_size DESC, dg.id ASC, dgf.is_canonical DESC;
            """)
            rows = cur.fetchall()

            groups_dict: Dict[int, Dict[str, Any]] = {}
            for r in rows:
                gid = r["group_id"]
                if gid not in groups_dict:
                    groups_dict[gid] = {
                        "group_id": gid,
                        "group_hash": r["group_hash"],
                        "file_size": r["file_size"],
                        "file_count": r["file_count"],
                        "reclaimable_size": r["reclaimable_size"],
                        "created_at": r["group_created_at"],
                        "files": [],
                    }
                groups_dict[gid]["files"].append({
                    "file_id": r["file_id"],
                    "filename": r["filename"],
                    "path": r["path"],
                    "extension": r["extension"],
                    "type": r["type"],
                    "modified_at": r["modified_at"],
                    "content_hash": r["content_hash"],
                    "hash_status": r["hash_status"],
                    "is_canonical": bool(r["is_canonical"]),
                })

            raw_groups = list(groups_dict.values())
            if root_paths is None:
                return raw_groups

            if not root_paths:
                return []

            norm_roots = [os.path.normpath(r) for r in root_paths]
            scoped_groups = []
            for g in raw_groups:
                matched_files = [f for f in g["files"] if is_path_under_roots(f["path"], norm_roots)]
                if len(matched_files) >= 2:
                    k = len(matched_files)
                    reclaimable = (k - 1) * g["file_size"]
                    sorted_files = sorted(
                        matched_files,
                        key=lambda x: (x.get("modified_at") or "", len(x["path"]))
                    )
                    for idx, sf in enumerate(sorted_files):
                        sf["is_canonical"] = (idx == 0)

                    g_scoped = dict(g)
                    g_scoped["file_count"] = k
                    g_scoped["reclaimable_size"] = reclaimable
                    g_scoped["files"] = sorted_files
                    scoped_groups.append(g_scoped)

            return scoped_groups
        finally:
            conn.close()

    # ==========================================
    # Scan History
    # ==========================================

    def record_scan_start(self, root_path: str) -> int:
        """Record beginning of a scan, returning scan_id."""
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                INSERT INTO scan_history (root_path, started_at, status)
                VALUES (?, ?, 'RUNNING');
            """, (os.path.normpath(root_path), now))
            return cur.lastrowid

    def record_scan_completion(
        self,
        scan_id: int,
        files_scanned: int,
        folders_scanned: int,
        bytes_scanned: int,
        status: str = "COMPLETED",
        error_count: int = 0,
    ) -> None:
        """Update scan_history on completion or cancellation."""
        now = datetime.now().isoformat()
        with self.transaction() as cur:
            cur.execute("""
                UPDATE scan_history
                SET completed_at = ?,
                    files_scanned = ?,
                    folders_scanned = ?,
                    bytes_scanned = ?,
                    status = ?,
                    error_count = ?
                WHERE id = ?;
            """, (now, files_scanned, folders_scanned, bytes_scanned, status, error_count, scan_id))

    def get_scan_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent scan history logs."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM scan_history
                ORDER BY id DESC
                LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_latest_successful_scan(self, root_paths: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Fetch the most recent completed scan, optionally scoped to root_paths."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM scan_history
                WHERE status = 'COMPLETED'
                ORDER BY id DESC;
            """)
            rows = [dict(r) for r in cur.fetchall()]
            if not rows:
                return None
            if root_paths is None:
                return rows[0]
            if not root_paths:
                return None
            norm_roots = [os.path.normpath(r) for r in root_paths]
            for r in rows:
                if is_path_under_roots(r["root_path"], norm_roots):
                    return r
            return None
        finally:
            conn.close()

    # ==========================================
    # Aggregated Summary Stats
    # ==========================================

    def get_dashboard_summary(self, root_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compute live aggregated metrics from database, optionally scoped to active root_paths."""
        if root_paths is not None and len(root_paths) == 0:
            return {
                "total_files": 0,
                "total_size": 0,
                "total_bytes": 0,
                "total_folders": 0,
                "duplicate_groups": 0,
                "redundant_copies": 0,
                "duplicate_files_count": 0,
                "reclaimable_size": 0,
                "reclaimable_bytes": 0,
                "extension_stats": [],
                "category_stats": [],
                "last_scan": None,
                "is_empty_selection": True,
            }

        scoped_files = self.get_files_for_roots(root_paths)
        scoped_folders = self.get_folders_for_roots(root_paths)
        dup_groups = self.get_duplicate_groups_with_files(root_paths=root_paths)

        total_files = len(scoped_files)
        total_size = sum(f["size"] for f in scoped_files)
        total_folders = len(scoped_folders)
        dup_group_count = len(dup_groups)
        redundant_copies = sum(len(g["files"]) - 1 for g in dup_groups)
        reclaimable_bytes = sum(g["reclaimable_size"] for g in dup_groups)

        # Extension distribution computed directly from scoped_files
        ext_map: Dict[str, Dict[str, Any]] = {}
        for f in scoped_files:
            ext = f.get("extension") or ""
            if ext not in ext_map:
                ext_map[ext] = {"extension": ext, "count": 0, "total_size": 0}
            ext_map[ext]["count"] += 1
            ext_map[ext]["total_size"] += f["size"]
        ext_stats = sorted(ext_map.values(), key=lambda x: x["total_size"], reverse=True)[:10]

        # Category distribution computed directly from scoped_files
        cat_map: Dict[str, Dict[str, Any]] = {}
        for f in scoped_files:
            cat = f.get("type") or "Other"
            if cat not in cat_map:
                cat_map[cat] = {"type": cat, "count": 0, "total_size": 0}
            cat_map[cat]["count"] += 1
            cat_map[cat]["total_size"] += f["size"]
        cat_stats = sorted(cat_map.values(), key=lambda x: x["count"], reverse=True)

        last_scan = self.get_latest_successful_scan(root_paths=root_paths)

        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_bytes": total_size,
            "total_folders": total_folders,
            "duplicate_groups": dup_group_count,
            "redundant_copies": redundant_copies,
            "duplicate_files_count": redundant_copies,
            "reclaimable_size": reclaimable_bytes,
            "reclaimable_bytes": reclaimable_bytes,
            "extension_stats": ext_stats,
            "category_stats": cat_stats,
            "last_scan": last_scan,
            "is_empty_selection": False,
        }
