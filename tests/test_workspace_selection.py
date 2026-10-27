"""
Comprehensive Test Suite for Selected Folders Workspace Feature (FileSense).
Verifies the 10 specification scenarios:
1. Scenario 1: Only Folder A selected -> results match Folder A only.
2. Scenario 2: Both Folder A & B selected -> results combine both folders.
3. Scenario 3: Deselect Folder B -> results revert to Folder A only.
4. Scenario 4: Cross-folder duplicates between A & B appear only when both are selected.
5. Scenario 5: Deselecting Folder B removes cross-folder duplicate groups and reclaimable storage.
6. Scenario 6: Internal duplicates within Folder A still appear when Folder A is selected alone.
7. Scenario 7: Selecting parent folder and child folder does not double-count files.
8. Scenario 8: Deselecting all folders shows empty workspace state without crashing.
9. Scenario 9: Application restart preserves folder selection states in SQLite.
10. Scenario 10: Incremental file add/delete in Folder A updates metrics without affecting unselected Folder B.
"""

import os
import shutil
import tempfile
import unittest

from app.database import DatabaseManager, is_path_under_roots
from app.scanner import DirectoryScanner
from app.duplicate_detector import DuplicateDetector
from app.file_index import FileIndex
from app.storage_optimizer import StorageOptimizer


class TestWorkspaceSelectionScenarios(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="filesense_ws_test_")

        # Folder A setup
        self.folder_a = os.path.join(self.temp_dir, "FolderA")
        os.makedirs(self.folder_a, exist_ok=True)
        self.file_a_unique = os.path.join(self.folder_a, "unique_a.txt")
        with open(self.file_a_unique, "w", encoding="utf-8") as f:
            f.write("Unique content for Folder A only")

        # Folder A internal duplicates
        self.file_a_dup1 = os.path.join(self.folder_a, "internal_dup1.pdf")
        self.file_a_dup2 = os.path.join(self.folder_a, "internal_dup2.pdf")
        dup_content = "Identical internal content inside folder A for duplicates" * 5
        with open(self.file_a_dup1, "w", encoding="utf-8") as f:
            f.write(dup_content)
        with open(self.file_a_dup2, "w", encoding="utf-8") as f:
            f.write(dup_content)

        # Cross-folder duplicate in A
        self.cross_content = "Cross folder duplicate content shared between A and B" * 4
        self.file_a_cross = os.path.join(self.folder_a, "cross_shared.dat")
        with open(self.file_a_cross, "w", encoding="utf-8") as f:
            f.write(self.cross_content)

        # Folder B setup
        self.folder_b = os.path.join(self.temp_dir, "FolderB")
        os.makedirs(self.folder_b, exist_ok=True)
        self.file_b_unique = os.path.join(self.folder_b, "unique_b.txt")
        with open(self.file_b_unique, "w", encoding="utf-8") as f:
            f.write("Unique content for Folder B only")

        # Cross-folder duplicate in B
        self.file_b_cross = os.path.join(self.folder_b, "cross_shared.dat")
        with open(self.file_b_cross, "w", encoding="utf-8") as f:
            f.write(self.cross_content)

        # Parent & Child folder setup
        self.folder_parent = os.path.join(self.temp_dir, "ParentFolder")
        self.folder_child = os.path.join(self.folder_parent, "ChildSubfolder")
        os.makedirs(self.folder_child, exist_ok=True)
        self.file_parent = os.path.join(self.folder_parent, "parent_file.txt")
        with open(self.file_parent, "w", encoding="utf-8") as f:
            f.write("Parent folder file")
        self.file_child = os.path.join(self.folder_child, "child_file.txt")
        with open(self.file_child, "w", encoding="utf-8") as f:
            f.write("Child subfolder file")

        # Database and tools setup
        self.db_path = os.path.join(self.temp_dir, "workspace_test.db")
        self.db = DatabaseManager(self.db_path)
        self.scanner = DirectoryScanner(self.db)
        self.detector = DuplicateDetector(self.db)
        self.optimizer = StorageOptimizer(self.db)
        self.file_index = FileIndex()

        # Scan Folder A and Folder B into the database
        self.scanner.scan_directory(self.folder_a)
        self.scanner.scan_directory(self.folder_b)

        # Register roots
        self.root_a_info = self.db.add_workspace_root(self.folder_a, is_selected=True)
        self.root_b_info = self.db.add_workspace_root(self.folder_b, is_selected=True)
        self.root_a_id = self.root_a_info["id"]
        self.root_b_id = self.root_b_info["id"]

        # Run duplicate detection across entire DB once to populate content hashes and duplicate tables
        self.detector.detect_duplicates(min_size=1, verify_bytes=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_only_folder_a_selected(self):
        """Scenario 1: When only Folder A is selected, results match Folder A only."""
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, False)

        selected_roots = self.db.get_selected_root_paths()
        self.assertEqual(len(selected_roots), 1)
        self.assertEqual(selected_roots[0], os.path.normpath(self.folder_a))

        files = self.db.get_files_for_roots(selected_roots)
        # Folder A contains 4 files: unique_a, dup1, dup2, cross_shared
        self.assertEqual(len(files), 4)
        for f in files:
            self.assertTrue(is_path_under_roots(f["path"], selected_roots))
            self.assertNotIn(os.path.normpath(self.folder_b), os.path.normpath(f["path"]))

        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        self.assertEqual(summary["total_files"], 4)
        self.assertFalse(summary["is_empty_selection"])

    def test_02_both_folders_selected(self):
        """Scenario 2: When Folder A and Folder B are selected, results combine both folders."""
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, True)

        selected_roots = self.db.get_selected_root_paths()
        self.assertEqual(len(selected_roots), 2)

        files = self.db.get_files_for_roots(selected_roots)
        # Folder A (4) + Folder B (2) = 6 files
        self.assertEqual(len(files), 6)

        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        self.assertEqual(summary["total_files"], 6)

    def test_03_deselect_folder_b_reverts_to_a(self):
        """Scenario 3: Deselecting Folder B reverts results to Folder A only without deleting B's data."""
        # Start with both
        self.db.set_all_workspace_roots_selected(True)
        self.assertEqual(len(self.db.get_files_for_roots(self.db.get_selected_root_paths())), 6)

        # Deselect B
        self.db.set_workspace_root_selected(self.root_b_id, False)
        selected_roots = self.db.get_selected_root_paths()
        self.assertEqual(len(selected_roots), 1)

        files = self.db.get_files_for_roots(selected_roots)
        self.assertEqual(len(files), 4)

        # Verify Folder B's records are NOT deleted from SQLite
        all_db_files = self.db.get_all_files()
        self.assertEqual(len(all_db_files), 6)

    def test_04_cross_folder_duplicates_appear_only_when_both_selected(self):
        """Scenario 4: Cross-folder duplicates between A and B appear only when both are selected."""
        # Both selected
        self.db.set_all_workspace_roots_selected(True)
        selected_roots = self.db.get_selected_root_paths()
        dup_groups = self.db.get_duplicate_groups_with_files(root_paths=selected_roots)

        # Should find 2 groups: internal in A (2 files) and cross-folder between A and B (2 files)
        self.assertEqual(len(dup_groups), 2)

        # Check cross-folder group
        group_cross = None
        for g in dup_groups:
            paths = [f["path"] for f in g["files"]]
            has_a = any(is_path_under_roots(p, [self.folder_a]) for p in paths)
            has_b = any(is_path_under_roots(p, [self.folder_b]) for p in paths)
            if has_a and has_b:
                group_cross = g
                break

        self.assertIsNotNone(group_cross, "Cross-folder duplicate group should be found when both A and B are selected")
        self.assertEqual(len(group_cross["files"]), 2)

    def test_05_deselecting_folder_removes_cross_folder_duplicates(self):
        """Scenario 5: When Folder B is deselected, cross-folder duplicates disappear from duplicate groups and do not count toward recoverable space."""
        # Deselect B
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, False)
        selected_roots = self.db.get_selected_root_paths()

        dup_groups = self.db.get_duplicate_groups_with_files(root_paths=selected_roots)
        # Only internal duplicates in A should remain (1 group)
        self.assertEqual(len(dup_groups), 1)

        group_files = dup_groups[0]["files"]
        for f in group_files:
            self.assertTrue(is_path_under_roots(f["path"], [self.folder_a]))

        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        # 1 group of 2 files -> 1 redundant copy
        self.assertEqual(summary["duplicate_files_count"], 1)

    def test_06_internal_duplicates_persist_when_folder_selected_alone(self):
        """Scenario 6: Internal duplicates within a single folder still appear when that folder is selected alone."""
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, False)

        groups = self.db.get_duplicate_groups_with_files(root_paths=[self.folder_a])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["file_count"], 2)
        filenames = [f["filename"] for f in groups[0]["files"]]
        self.assertIn("internal_dup1.pdf", filenames)
        self.assertIn("internal_dup2.pdf", filenames)

    def test_07_parent_and_child_overlap_no_double_counting(self):
        """Scenario 7: If a parent folder and child folder are both selected, each physical file is counted only once."""
        self.scanner.scan_directory(self.folder_parent)
        self.root_p_id = self.db.add_workspace_root(self.folder_parent, is_selected=True)["id"]
        self.root_c_id = self.db.add_workspace_root(self.folder_child, is_selected=True)["id"]

        selected_roots = [self.folder_parent, self.folder_child]
        files = self.db.get_files_for_roots(selected_roots)

        # ParentFolder has parent_file.txt and ChildSubfolder/child_file.txt
        # Total files in ParentFolder is 2. Selecting both must NOT yield 3 files!
        self.assertEqual(len(files), 2)
        filenames = [f["filename"] for f in files]
        self.assertEqual(sorted(filenames), ["child_file.txt", "parent_file.txt"])

        # In dashboard summary
        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        self.assertEqual(summary["total_files"], 2)

    def test_08_empty_selection_handling(self):
        """Scenario 8: Deselecting all folders shows a clear empty workspace state without crashing."""
        self.db.set_all_workspace_roots_selected(False)
        selected_roots = self.db.get_selected_root_paths()
        self.assertEqual(selected_roots, [])

        files = self.db.get_files_for_roots(selected_roots)
        self.assertEqual(files, [])

        folders = self.db.get_folders_for_roots(selected_roots)
        self.assertEqual(folders, [])

        dup_groups = self.db.get_duplicate_groups_with_files(root_paths=selected_roots)
        self.assertEqual(dup_groups, [])

        summary = self.db.get_dashboard_summary(root_paths=selected_roots)
        self.assertTrue(summary["is_empty_selection"])
        self.assertEqual(summary["total_files"], 0)
        self.assertEqual(summary["total_bytes"], 0)
        self.assertEqual(summary["duplicate_files_count"], 0)
        self.assertEqual(summary["reclaimable_bytes"], 0)

        # Cleanup plan on empty roots
        plan = self.optimizer.generate_cleanup_plan(root_paths=[])
        self.assertEqual(plan["total_redundant_files"], 0)
        self.assertEqual(plan["total_reclaimable_bytes"], 0)
        self.assertEqual(plan["cleanup_candidates"], [])

    def test_09_persistence_across_restarts(self):
        """Scenario 9: Application restart preserves folder selections in SQLite."""
        # Select A, deselect B
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, False)

        # Simulate new application instance opening same database
        new_db_instance = DatabaseManager(self.db_path)
        selected = new_db_instance.get_selected_root_paths()
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0], os.path.normpath(self.folder_a))

        roots = new_db_instance.get_workspace_roots()
        root_map = {os.path.normpath(r["path"]): r["is_selected"] for r in roots}
        self.assertEqual(root_map[os.path.normpath(self.folder_a)], 1)
        self.assertEqual(root_map[os.path.normpath(self.folder_b)], 0)

    def test_10_rescan_after_file_modifications(self):
        """Scenario 10: Adding/deleting files in Folder A followed by rescan updates metrics without affecting unselected Folder B."""
        # Select A only
        self.db.set_workspace_root_selected(self.root_a_id, True)
        self.db.set_workspace_root_selected(self.root_b_id, False)

        # Add a new file to Folder A
        new_file = os.path.join(self.folder_a, "added_new.log")
        with open(new_file, "w", encoding="utf-8") as f:
            f.write("Log file line 1\nLog file line 2\n")

        # Delete unique_a.txt from disk
        os.remove(self.file_a_unique)

        # Rescan Folder A incrementally
        res = self.scanner.scan_directory(self.folder_a, incremental=True)
        self.assertEqual(res["status"], "COMPLETED")

        # Folder A should now have: dup1, dup2, cross_shared, added_new.log = 4 files
        selected_roots = self.db.get_selected_root_paths()
        files = self.db.get_files_for_roots(selected_roots)
        filenames = [f["filename"] for f in files]
        self.assertIn("added_new.log", filenames)
        self.assertNotIn("unique_a.txt", filenames)
        self.assertEqual(len(files), 4)

        # Unselected Folder B in DB should remain completely unaffected (2 files)
        b_files = self.db.get_files_for_roots([self.folder_b])
        self.assertEqual(len(b_files), 2)


if __name__ == "__main__":
    unittest.main()
