"""
In-Memory Hash Table Indexes for High-Performance File Search.
DSA-II Project Requirement: Hash Table (Dictionary) Indexing & Average O(1) Lookups.
"""

from typing import Dict, List, Optional, Set, Any
import os
from datetime import datetime


class FileIndex:
    """
    Maintains multiple hash-table indexes in memory for lightning-fast queries.
    
    Hash Tables:
    - filename_index: lower(filename) -> List[file_id]  [O(1) exact lookup]
    - extension_index: lower(extension) -> List[file_id] [O(1) exact lookup]
    - size_index: size_in_bytes -> List[file_id]        [O(1) exact lookup]
    - content_hash_index: sha256_hash -> List[file_id]  [O(1) exact lookup]
    - path_index: normpath -> file_id                   [O(1) exact lookup]
    - records: file_id -> FileDict                      [O(1) record retrieval]
    """

    def __init__(self):
        self.filename_index: Dict[str, List[int]] = {}
        self.extension_index: Dict[str, List[int]] = {}
        self.size_index: Dict[int, List[int]] = {}
        self.content_hash_index: Dict[str, List[int]] = {}
        self.path_index: Dict[str, int] = {}
        self.records: Dict[int, Dict[str, Any]] = {}
        self.duplicate_file_ids: Set[int] = set()

    def clear(self) -> None:
        """Clear all in-memory indexes."""
        self.filename_index.clear()
        self.extension_index.clear()
        self.size_index.clear()
        self.content_hash_index.clear()
        self.path_index.clear()
        self.records.clear()
        self.duplicate_file_ids.clear()

    def add_file(self, file_record: Dict[str, Any]) -> None:
        """
        Index a single file record across all hash tables.
        Time complexity: O(1) average case insertion per hash table.
        """
        file_id = file_record["id"]
        norm_path = os.path.normpath(file_record["path"])
        filename = file_record["filename"].lower()
        extension = (file_record.get("extension") or "").lower()
        size = file_record["size"]
        content_hash = file_record.get("content_hash")

        # Save record
        self.records[file_id] = file_record
        self.path_index[norm_path] = file_id

        # Filename index
        if filename not in self.filename_index:
            self.filename_index[filename] = []
        if file_id not in self.filename_index[filename]:
            self.filename_index[filename].append(file_id)

        # Extension index
        if extension not in self.extension_index:
            self.extension_index[extension] = []
        if file_id not in self.extension_index[extension]:
            self.extension_index[extension].append(file_id)

        # Size index
        if size not in self.size_index:
            self.size_index[size] = []
        if file_id not in self.size_index[size]:
            self.size_index[size].append(file_id)

        # Content hash index
        if content_hash:
            if content_hash not in self.content_hash_index:
                self.content_hash_index[content_hash] = []
            if file_id not in self.content_hash_index[content_hash]:
                self.content_hash_index[content_hash].append(file_id)

    def load_from_records(self, records: List[Dict[str, Any]]) -> None:
        """Rebuild in-memory indexes from a list of records (e.g. loaded from SQLite)."""
        self.clear()
        for r in records:
            self.add_file(r)

    def set_duplicate_file_ids(self, ids: Set[int]) -> None:
        """Mark set of file_ids as participating in duplicate groups."""
        self.duplicate_file_ids = set(ids)

    def get_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve record by ID in O(1)."""
        return self.records.get(file_id)

    def get_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve record by normalized path in O(1)."""
        norm_path = os.path.normpath(path)
        file_id = self.path_index.get(norm_path)
        if file_id:
            return self.records.get(file_id)
        return None

    def search_exact_filename(self, filename: str) -> List[Dict[str, Any]]:
        """O(1) exact filename search using filename_index."""
        key = filename.strip().lower()
        ids = self.filename_index.get(key, [])
        return [self.records[fid] for fid in ids if fid in self.records]

    def search_exact_extension(self, extension: str) -> List[Dict[str, Any]]:
        """O(1) exact extension search using extension_index."""
        key = extension.strip().lower()
        if not key.startswith(".") and key:
            key = "." + key
        ids = self.extension_index.get(key, [])
        return [self.records[fid] for fid in ids if fid in self.records]

    def search_exact_size(self, size_bytes: int) -> List[Dict[str, Any]]:
        """O(1) exact size search using size_index."""
        ids = self.size_index.get(size_bytes, [])
        return [self.records[fid] for fid in ids if fid in self.records]

    def search_exact_hash(self, sha256_hash: str) -> List[Dict[str, Any]]:
        """O(1) exact content hash search using content_hash_index."""
        key = sha256_hash.strip().lower()
        ids = self.content_hash_index.get(key, [])
        return [self.records[fid] for fid in ids if fid in self.records]

    def multi_criteria_search(
        self,
        query: Optional[str] = None,
        extension: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        category: Optional[str] = None,
        path_prefix: Optional[str] = None,
        duplicates_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Compound multi-criteria search combining hash table lookups with filtering.
        Optimized to use the narrowest initial candidate set first.
        """
        # Step 1: Candidate set selection
        candidate_ids: Optional[Set[int]] = None

        # If exact extension specified, use O(1) extension index
        if extension and extension.strip():
            ext_key = extension.strip().lower()
            if not ext_key.startswith("."):
                ext_key = "." + ext_key
            ext_ids = set(self.extension_index.get(ext_key, []))
            candidate_ids = ext_ids

        # If duplicate only specified, intersect with duplicate set
        if duplicates_only:
            if candidate_ids is None:
                candidate_ids = set(self.duplicate_file_ids)
            else:
                candidate_ids &= self.duplicate_file_ids

        # If no specific hash-index set was selected yet, start with all record IDs
        if candidate_ids is None:
            candidate_ids = set(self.records.keys())

        # Step 2: Filtering on the candidate subset
        results: List[Dict[str, Any]] = []
        norm_prefix = os.path.normpath(path_prefix) if path_prefix else None
        clean_query = query.strip().lower() if query else None

        for fid in candidate_ids:
            record = self.records.get(fid)
            if not record:
                continue

            # Query substring match (in filename or path)
            if clean_query:
                if clean_query not in record["filename"].lower() and clean_query not in record["path"].lower():
                    continue

            # Size filtering
            if min_size is not None and record["size"] < min_size:
                continue
            if max_size is not None and record["size"] > max_size:
                continue

            # Category filtering
            if category and category != "All":
                if record.get("type") != category:
                    continue

            # Path prefix filtering (folder subtree)
            if norm_prefix:
                r_path = os.path.normpath(record["path"])
                if not (r_path == norm_prefix or r_path.startswith(norm_prefix + os.sep)):
                    continue

            # Tag duplicate status in result
            rec_copy = dict(record)
            rec_copy["is_duplicate"] = fid in self.duplicate_file_ids
            results.append(rec_copy)

        return results

    def sort_results(
        self,
        results: List[Dict[str, Any]],
        sort_by: str = "filename",
        descending: bool = False,
    ) -> List[Dict[str, Any]]:
        """Sort search results by field."""
        if sort_by == "size":
            key_func = lambda x: x.get("size", 0)
        elif sort_by == "extension":
            key_func = lambda x: (x.get("extension") or "").lower()
        elif sort_by == "modified_at":
            key_func = lambda x: x.get("modified_at") or ""
        elif sort_by == "type":
            key_func = lambda x: x.get("type", "")
        else:
            key_func = lambda x: x.get("filename", "").lower()

        return sorted(results, key=key_func, reverse=descending)

    def get_total_indexed(self) -> int:
        """Return total number of indexed files."""
        return len(self.records)

    def get_total_size(self) -> int:
        """Return total bytes of all indexed files."""
        return sum(r.get("size", 0) for r in self.records.values())
