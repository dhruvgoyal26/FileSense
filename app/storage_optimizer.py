"""
Safe Storage Cleanup Optimizer.
Identifies redundant file copies, retains canonical master copies,
generates safe non-destructive recommendations, provides CSV export,
and supports budget-constrained cleanup planning via 0/1 Knapsack DP.
"""

import os
import csv
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from app.database import DatabaseManager
from app.hashing import calculate_file_hash, verify_identical_bytes
from app.dynamic_programming import solve_knapsack_01


class StorageOptimizer:
    """
    Manages safe file cleanup recommendations with strict integrity validation.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def generate_cleanup_plan(
        self,
        canonical_strategy: str = "oldest",  # 'oldest', 'newest', 'shortest_path'
        root_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate safe cleanup recommendations from database duplicate groups,
        optionally scoped to root_paths.
        """
        dup_groups = self.db.get_duplicate_groups_with_files(root_paths=root_paths)

        total_reclaimable_bytes = 0
        total_redundant_files = 0
        plan_groups: List[Dict[str, Any]] = []
        cleanup_candidates: List[Dict[str, Any]] = []

        for g in dup_groups:
            files = g["files"]
            if len(files) < 2:
                continue

            file_size = g["file_size"]
            group_id = g["group_id"]
            group_hash = g["group_hash"]

            # Sort files according to canonical strategy
            if canonical_strategy == "newest":
                sorted_files = sorted(files, key=lambda f: f.get("modified_at") or "", reverse=True)
            elif canonical_strategy == "shortest_path":
                sorted_files = sorted(files, key=lambda f: len(f["path"]))
            else:  # default: oldest
                sorted_files = sorted(files, key=lambda f: f.get("modified_at") or "")

            canonical_file = sorted_files[0]
            redundant_files = sorted_files[1:]

            group_reclaimable = len(redundant_files) * file_size
            total_reclaimable_bytes += group_reclaimable
            total_redundant_files += len(redundant_files)

            # Build list of cleanup candidate actions
            for rf in redundant_files:
                candidate_action = {
                    "action_id": f"group_{group_id}_file_{rf['file_id']}",
                    "group_id": group_id,
                    "group_hash": group_hash,
                    "file_id": rf["file_id"],
                    "filename": rf["filename"],
                    "path": rf["path"],
                    "extension": rf["extension"],
                    "size": file_size,
                    "canonical_path": canonical_file["path"],
                    "selected_for_cleanup": True,
                }
                cleanup_candidates.append(candidate_action)

            plan_groups.append({
                "group_id": group_id,
                "group_hash": group_hash,
                "file_size": file_size,
                "file_count": len(files),
                "reclaimable_size": group_reclaimable,
                "canonical_file": canonical_file,
                "redundant_files": redundant_files,
            })

        return {
            "canonical_strategy": canonical_strategy,
            "group_count": len(plan_groups),
            "total_redundant_files": total_redundant_files,
            "total_reclaimable_bytes": total_reclaimable_bytes,
            "groups": plan_groups,
            "cleanup_candidates": cleanup_candidates,
        }

    def optimize_with_knapsack_budget(
        self,
        cleanup_candidates: List[Dict[str, Any]],
        budget_bytes: int,
    ) -> Dict[str, Any]:
        """
        Use 0/1 Knapsack DP to select the optimal subset of cleanup actions
        under a storage or target reclamation budget.
        
        To prevent selecting multiple copies from the same duplicate group,
        we pick at most 1 redundant copy per group as primary item, or prioritize by size.
        """
        # Ensure independence: select at most 1 representative redundant copy per duplicate group
        group_to_candidate: Dict[int, Dict[str, Any]] = {}
        for c in cleanup_candidates:
            gid = c["group_id"]
            if gid not in group_to_candidate:
                group_to_candidate[gid] = c

        independent_items = []
        for gid, cand in group_to_candidate.items():
            # Utility can be modeled as size in KB or user priority
            utility_score = max(1, cand["size"] // 1024)
            independent_items.append({
                "name": cand["filename"],
                "path": cand["path"],
                "size": cand["size"],
                "utility": utility_score,
                "group_id": gid,
                "candidate_ref": cand,
            })

        dp_result = solve_knapsack_01(independent_items, budget_bytes)
        return dp_result

    def export_recommendations_csv(
        self,
        cleanup_candidates: List[Dict[str, Any]],
        output_csv_path: str,
    ) -> int:
        """
        Export cleanup recommendations safely to a CSV file.
        Returns number of rows written.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
        rows_written = 0

        with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # Header
            writer.writerow([
                "Group ID",
                "Group SHA256",
                "Redundant File ID",
                "Redundant File Name",
                "Redundant File Path",
                "File Size (Bytes)",
                "Retained Master File Path",
                "Generated At",
            ])

            now = datetime.now().isoformat()
            for c in cleanup_candidates:
                writer.writerow([
                    c.get("group_id"),
                    c.get("group_hash"),
                    c.get("file_id"),
                    c.get("filename"),
                    c.get("path"),
                    c.get("size"),
                    c.get("canonical_path"),
                    now,
                ])
                rows_written += 1

        return rows_written

    def safe_delete_file(
        self,
        target_path: str,
        expected_size: int,
        expected_hash: str,
        canonical_path: str,
    ) -> Tuple[bool, str]:
        """
        Safely delete a confirmed redundant file after exhaustive integrity verification.
        
        Guarantees:
        1. Canonical master file MUST exist on disk.
        2. Canonical master file size and hash must match expected values.
        3. Target redundant file MUST exist on disk.
        4. Target redundant file size and hash must match expected values.
        5. Target and canonical must not be the identical path!
        """
        norm_target = os.path.normpath(target_path)
        norm_canon = os.path.normpath(canonical_path)

        if norm_target == norm_canon:
            return False, "Target is identical to canonical master file. Deletion forbidden."

        if not os.path.exists(norm_canon):
            return False, "Canonical master file does not exist. Aborting to prevent data loss."

        if not os.path.exists(norm_target):
            return False, "Target file no longer exists on disk."

        # Verify target file size
        if os.path.getsize(norm_target) != expected_size:
            return False, "Target file size has changed since index. Aborting."

        # Verify target file hash
        h_target, status = calculate_file_hash(norm_target)
        if status != "SUCCESS" or h_target != expected_hash:
            return False, f"Target hash mismatch or read error ({status}). Aborting."

        # Verify canonical file hash
        h_canon, status_c = calculate_file_hash(norm_canon)
        if status_c != "SUCCESS" or h_canon != expected_hash:
            return False, f"Canonical master file hash invalid ({status_c}). Aborting."

        # Verify byte equality
        if not verify_identical_bytes(norm_canon, norm_target):
            return False, "Byte-level verification failed between target and master."

        # Safe removal
        try:
            os.remove(norm_target)
            return True, "Successfully deleted confirmed redundant file."
        except (PermissionError, OSError) as e:
            return False, f"OS deletion error: {e}"
