"""
Tests for Tree Data Structure and Directory Scanner.
Covers Requirements:
1. Directory tree construction
2. Recursive discovery of nested files
19. Missing or inaccessible files
20. Incremental indexing after a file changes
"""

import unittest
import tempfile
import os
import shutil
import time
from pathlib import Path

from app.tree_structure import TreeNode, DirectoryTree
from app.database import DatabaseManager
from app.scanner import DirectoryScanner


class TestTreeStructureAndScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="filesense_tree_test_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseManager(self.db_path)
        self.scanner = DirectoryScanner(self.db)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_tree_construction_and_traversal(self):
        """Test 1: Directory tree construction and recursive metrics."""
        tree = DirectoryTree(self.temp_dir)
        self.assertIsNotNone(tree.root)
        self.assertTrue(tree.root.is_directory)

        # Insert nested paths
        file1_path = os.path.join(self.temp_dir, "sub1", "file1.txt")
        file2_path = os.path.join(self.temp_dir, "sub1", "sub2", "file2.txt")

        node1 = tree.insert_path(file1_path, is_directory=False, size=500)
        node2 = tree.insert_path(file2_path, is_directory=False, size=1500)

        self.assertEqual(node1.size, 500)
        self.assertEqual(node2.size, 1500)
        self.assertEqual(tree.get_total_size(), 2000)

        # Test traversal
        preorder_nodes = list(tree.root.traverse_preorder())
        self.assertGreaterEqual(len(preorder_nodes), 4)  # root, sub1, file1, sub2, file2

        postorder_nodes = list(tree.root.traverse_postorder())
        self.assertEqual(postorder_nodes[-1], tree.root)

        # Count nodes
        files_count, folders_count = tree.count_nodes()
        self.assertEqual(files_count, 2)
        self.assertEqual(folders_count, 3)  # root, sub1, sub2

    def test_02_recursive_discovery_of_nested_files(self):
        """Test 2: Recursive discovery of nested files and folders."""
        scan_folder = os.path.join(self.temp_dir, "scan_root")
        os.makedirs(os.path.join(scan_folder, "a", "b", "c"), exist_ok=True)

        # Create files at different levels
        with open(os.path.join(scan_folder, "root_file.txt"), "w") as f:
            f.write("Root content")
        with open(os.path.join(scan_folder, "a", "file_a.txt"), "w") as f:
            f.write("A content")
        with open(os.path.join(scan_folder, "a", "b", "c", "file_c.txt"), "w") as f:
            f.write("C content deep")

        result = self.scanner.scan_directory(scan_folder)

        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["files_count"], 3)
        self.assertGreaterEqual(result["folders_count"], 4)

        # Verify database records
        db_files = self.db.get_all_files()
        self.assertEqual(len(db_files), 3)

    def test_19_missing_or_inaccessible_directory(self):
        """Test 19: Safe handling of missing directory."""
        non_existent = os.path.join(self.temp_dir, "ghost_folder_12345")
        with self.assertRaises(FileNotFoundError):
            self.scanner.scan_directory(non_existent)

    def test_20_incremental_indexing_after_file_changes(self):
        """Test 20: Incremental indexing detects updates, additions, deletions."""
        scan_folder = os.path.join(self.temp_dir, "inc_root")
        os.makedirs(scan_folder, exist_ok=True)

        file1 = os.path.join(scan_folder, "file1.txt")
        file2 = os.path.join(scan_folder, "file2.txt")

        with open(file1, "w") as f:
            f.write("First version")
        with open(file2, "w") as f:
            f.write("File 2 unchanged")

        # Initial scan
        res1 = self.scanner.scan_directory(scan_folder, incremental=False)
        self.assertEqual(res1["files_count"], 2)

        # Sleep slightly to ensure distinct mtime timestamp
        time.sleep(0.05)

        # Modify file1, delete file2, add file3
        with open(file1, "w") as f:
            f.write("Modified version with more bytes and new length")
        os.remove(file2)

        file3 = os.path.join(scan_folder, "file3.txt")
        with open(file3, "w") as f:
            f.write("Brand new file")

        # Incremental scan
        res2 = self.scanner.scan_directory(scan_folder, incremental=True)
        self.assertEqual(res2["status"], "COMPLETED")
        self.assertEqual(res2["files_count"], 2)  # file1 and file3
        self.assertEqual(res2["deleted_count"], 1)  # file2 removed

        db_files = self.db.get_all_files()
        filenames = [f["filename"] for f in db_files]
        self.assertIn("file1.txt", filenames)
        self.assertIn("file3.txt", filenames)
        self.assertNotIn("file2.txt", filenames)


if __name__ == "__main__":
    unittest.main()
