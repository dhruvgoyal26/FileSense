"""
End-to-End Integration Test for FileSense.
Verifies the complete lifecycle:
1. Synthetic demo data generation
2. Directory scanning and DirectoryTree construction
3. SQLite persistence & in-memory hash indexing
4. Multi-criteria search
5. Multi-stage duplicate detection (size -> SHA-256 -> byte verification)
6. Duplicate graph construction & DFS/BFS traversal
7. 0/1 Knapsack DP storage optimization
8. Safe CSV export and verified redundant deletion
9. Benchmark comparison (Index vs Raw disk walk)
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from scripts.generate_demo_data import generate_demo_dataset
from app.database import DatabaseManager
from app.scanner import DirectoryScanner
from app.file_index import FileIndex
from app.duplicate_detector import DuplicateDetector
from app.graph_structure import Graph
from app.graph_algorithms import GraphAlgorithms
from app.storage_optimizer import StorageOptimizer
from app.benchmark import benchmark_search_comparison


class TestEndToEndWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.mkdtemp(prefix="filesense_e2e_")
        self.demo_dir = os.path.join(self.temp_root, "demo_dataset")
        generate_demo_dataset(self.demo_dir)

        self.db_path = os.path.join(self.temp_root, "e2e_filesense.db")
        self.db = DatabaseManager(self.db_path)
        self.file_index = FileIndex()
        self.scanner = DirectoryScanner(self.db)
        self.detector = DuplicateDetector(self.db)
        self.optimizer = StorageOptimizer(self.db)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_complete_pipeline(self):
        # 1. Scan directory
        scan_res = self.scanner.scan_directory(self.demo_dir)
        self.assertEqual(scan_res["status"], "COMPLETED")
        self.assertGreaterEqual(scan_res["files_count"], 10)
        self.assertGreaterEqual(scan_res["folders_count"], 6)

        # 2. SQLite records verification
        db_files = self.db.get_all_files()
        self.assertEqual(len(db_files), scan_res["files_count"])

        # 3. Load In-Memory Index
        self.file_index.load_from_records(db_files)
        self.assertEqual(self.file_index.get_total_indexed(), scan_res["files_count"])

        # 4. Multi-criteria Search
        search_pdf = self.file_index.multi_criteria_search(extension=".pdf")
        self.assertGreaterEqual(len(search_pdf), 1)

        search_notes = self.file_index.multi_criteria_search(query="notes")
        self.assertEqual(len(search_notes), 2)  # notes.txt and notes_copy.txt

        # 5. Multi-Stage Duplicate Detection
        dup_res = self.detector.detect_duplicates(verify_bytes=True)
        self.assertEqual(dup_res["status"], "COMPLETED")
        self.assertGreaterEqual(dup_res["total_groups"], 3)
        self.assertGreaterEqual(dup_res["total_redundant_copies"], 3)
        self.assertGreater(dup_res["total_reclaimable_bytes"], 0)

        # 6. Duplicate Graph Construction & Traversals
        dup_groups = self.db.get_duplicate_groups_with_files()
        graph = Graph.build_from_duplicate_groups(dup_groups)
        self.assertGreater(graph.vertex_count(), 0)
        self.assertGreater(graph.edge_count(), 0)

        dfs_res = GraphAlgorithms.dfs_traversal(graph)
        self.assertEqual(dfs_res["component_count"], len(dup_groups))

        bfs_res = GraphAlgorithms.bfs_traversal(graph)
        self.assertEqual(bfs_res["component_count"], len(dup_groups))

        # 7. Safe Cleanup Plan & 0/1 Knapsack
        plan = self.optimizer.generate_cleanup_plan()
        self.assertEqual(plan["group_count"], len(dup_groups))
        self.assertGreater(len(plan["cleanup_candidates"]), 0)

        knapsack_res = self.optimizer.optimize_with_knapsack_budget(
            plan["cleanup_candidates"],
            budget_bytes=50000,
        )
        self.assertGreaterEqual(knapsack_res["selected_count"], 1)

        # 8. CSV Export
        csv_path = os.path.join(self.temp_root, "export.csv")
        written = self.optimizer.export_recommendations_csv(plan["cleanup_candidates"], csv_path)
        self.assertEqual(written, len(plan["cleanup_candidates"]))
        self.assertTrue(os.path.exists(csv_path))

        # 9. Safe Verified Deletion
        # Pick one candidate action
        target_cand = plan["cleanup_candidates"][0]
        success, msg = self.optimizer.safe_delete_file(
            target_path=target_cand["path"],
            expected_size=target_cand["size"],
            expected_hash=target_cand["group_hash"],
            canonical_path=target_cand["canonical_path"],
        )
        self.assertTrue(success, f"Deletion failed: {msg}")
        self.assertFalse(os.path.exists(target_cand["path"]))
        self.assertTrue(os.path.exists(target_cand["canonical_path"]))  # Master copy safe!

        # 10. Benchmark comparison
        bench = benchmark_search_comparison(self.demo_dir, self.file_index, "notes")
        self.assertEqual(bench["indexed_match_count"], 2)
        self.assertGreaterEqual(bench["raw_match_count"], 1)

    def test_main_window_views_and_navigation(self):
        """Verify MainWindow registers exactly 6 core sections and switches cleanly."""
        from ui.main_window import MainWindow
        app = MainWindow(db_path=self.db_path)
        app.withdraw()
        try:
            expected_views = [
                "Dashboard",
                "File Explorer / File Index",
                "Search Files",
                "Duplicate Detection",
                "Storage Optimizer",
                "Scan History",
            ]
            self.assertEqual(len(app.views), 6)
            for v in expected_views:
                self.assertIn(v, app.views)
                app.switch_view(v)
                app.update_idletasks()
            self.assertEqual(app.active_nav, "Scan History")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
