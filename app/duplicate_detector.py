"""
Multi-Stage Accurate Duplicate Detection Pipeline.
Stage 1: Size grouping (Filter out unique sizes)
Stage 2: Chunked SHA-256 Hashing (Streaming 1 MiB chunks)
Stage 3: Full byte-for-byte verification (100% Collision-proof guarantee)
"""

import os
import threading
from typing import Dict, List, Optional, Callable, Set, Any, Tuple
from collections import defaultdict

from app.hashing import calculate_file_hash, verify_identical_bytes
from app.database import DatabaseManager
from app.graph_structure import Graph
from app.graph_algorithms import GraphAlgorithms


class DuplicateDetector:
    """
    Executes multi-stage duplicate detection pipeline on indexed files.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Cancel duplicate detection."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check cancellation state."""
        return self._cancel_event.is_set()

    def detect_duplicates(
        self,
        min_size: int = 0,
        type_filter: Optional[str] = None,
        verify_bytes: bool = True,
        root_paths: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run the 3-stage duplicate detection algorithm on files in database,
        optionally scoped to root_paths.
        """
        self._cancel_event.clear()
        if root_paths is not None:
            all_files = self.db.get_files_for_roots(root_paths)
        else:
            all_files = self.db.get_all_files()

        # Filter by minimum size and type
        candidate_files = []
        for f in all_files:
            if f["size"] < min_size:
                continue
            if type_filter and type_filter != "All" and f.get("type") != type_filter:
                continue
            candidate_files.append(f)

        total_candidates = len(candidate_files)

        # ==========================================================
        # STAGE 1: Size Grouping
        # DSA concept: Pigeonhole principle & Size partitioning
        # Files with different sizes cannot be identical copies.
        # ==========================================================
        if progress_callback:
            progress_callback("Stage 1: Size Grouping", 0, total_candidates)

        size_groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for f in candidate_files:
            size_groups[f["size"]].append(f)

        # Retain only sizes with 2 or more files
        potential_duplicate_files: List[Dict[str, Any]] = []
        for size, files in size_groups.items():
            if len(files) >= 2:
                potential_duplicate_files.extend(files)

        if progress_callback:
            progress_callback(
                "Stage 1 Complete",
                len(potential_duplicate_files),
                total_candidates,
            )

        # ==========================================================
        # STAGE 2: Chunked Content Hashing (SHA-256)
        # Calculates SHA-256 on candidate files with matching sizes
        # ==========================================================
        hash_groups: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)
        hashed_count = 0
        total_to_hash = len(potential_duplicate_files)

        for f in potential_duplicate_files:
            if self.is_cancelled():
                return {"status": "CANCELLED", "groups": []}

            file_id = f["id"]
            file_path = f["path"]
            file_size = f["size"]

            # If hash already computed and valid in database, reuse it
            content_hash = f.get("content_hash")
            hash_status = f.get("hash_status")

            if not content_hash or hash_status != "SUCCESS":
                content_hash, hash_status = calculate_file_hash(file_path)
                self.db.update_file_hash(file_id, content_hash, hash_status)
                f["content_hash"] = content_hash
                f["hash_status"] = hash_status

            hashed_count += 1
            if progress_callback and (hashed_count % 5 == 0 or hashed_count == total_to_hash):
                progress_callback("Stage 2: SHA-256 Hashing", hashed_count, total_to_hash)

            if content_hash and hash_status == "SUCCESS":
                hash_groups[(file_size, content_hash)].append(f)

        # Filter hash groups with at least 2 files
        confirmed_hash_groups: Dict[Tuple[int, str], List[Dict[str, Any]]] = {}
        for key, files in hash_groups.items():
            if len(files) >= 2:
                confirmed_hash_groups[key] = files

        # ==========================================================
        # STAGE 3: Full Verification & Graph DFS Connected Components
        # DSA concept: Construct equivalence graph among candidate files
        # and execute Depth-First Search (DFS) to discover connected components.
        # ==========================================================
        verified_groups: List[Dict[str, Any]] = []
        group_idx = 1
        total_reclaimable_bytes = 0
        total_redundant_copies = 0

        for (file_size, content_hash), files in confirmed_hash_groups.items():
            if self.is_cancelled():
                return {"status": "CANCELLED", "groups": []}

            # Build in-memory equivalence graph
            eq_graph = Graph(directed=False)
            id_to_file = {}
            for f in files:
                v_id = str(f["id"])
                eq_graph.add_vertex(v_id, data=f)
                id_to_file[v_id] = f

            # Add verified edges between files with identical content
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    f_a = files[i]
                    f_b = files[j]
                    if verify_bytes:
                        is_match = verify_identical_bytes(f_a["path"], f_b["path"])
                    else:
                        is_match = True
                    if is_match:
                        eq_graph.add_edge(str(f_a["id"]), str(f_b["id"]))

            # Discover duplicate clusters using Graph DFS traversal
            dfs_result = GraphAlgorithms.dfs_traversal(eq_graph)

            for component_v_ids in dfs_result["components"]:
                if len(component_v_ids) < 2:
                    continue

                cluster_files = [id_to_file[vid] for vid in component_v_ids if vid in id_to_file]
                if len(cluster_files) < 2:
                    continue

                # Sort files to determine canonical master copy (oldest, then shortest path)
                sorted_files = sorted(
                    cluster_files,
                    key=lambda x: (x.get("modified_at") or "", len(x["path"]))
                )
                canonical_file = sorted_files[0]
                k = len(sorted_files)
                reclaimable = (k - 1) * file_size

                # Update database verification status
                for f in sorted_files:
                    self.db.update_file_hash(f["id"], content_hash, "VERIFIED")

                group_data = {
                    "group_hash": content_hash,
                    "file_size": file_size,
                    "file_count": k,
                    "reclaimable_size": reclaimable,
                    "verification_status": "VERIFIED" if verify_bytes else "HASH_MATCHED",
                    "dfs_component_size": len(component_v_ids),
                    "files": [
                        {
                            "file_id": f["id"],
                            "filename": f["filename"],
                            "path": f["path"],
                            "extension": f["extension"],
                            "type": f["type"],
                            "modified_at": f["modified_at"],
                            "content_hash": content_hash,
                            "hash_status": "VERIFIED" if verify_bytes else "HASH_MATCHED",
                            "is_canonical": (f["id"] == canonical_file["id"]),
                        }
                        for f in sorted_files
                    ],
                }

                verified_groups.append(group_data)
                total_reclaimable_bytes += reclaimable
                total_redundant_copies += (k - 1)
                group_idx += 1

        # Persist duplicate groups into SQLite
        self.db.save_duplicate_groups(verified_groups)

        if progress_callback:
            progress_callback(
                "Complete",
                len(verified_groups),
                len(verified_groups),
            )

        return {
            "status": "COMPLETED",
            "groups": verified_groups,
            "total_groups": len(verified_groups),
            "total_redundant_copies": total_redundant_copies,
            "total_reclaimable_bytes": total_reclaimable_bytes,
        }
