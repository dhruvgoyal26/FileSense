"""
Tests for Accurate Duplicate Detection Pipeline.
Covers Requirements:
5. Exact duplicate detection when filenames differ
6. Correct rejection of same-sized files with different contents
7. Correct handling of empty files
And accurate calculation of reclaimable storage: (k - 1) * S.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from app.database import DatabaseManager
from app.scanner import DirectoryScanner
from app.duplicate_detector import DuplicateDetector


class TestDuplicateDetection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="filesense_dup_test_")
        self.db_path = os.path.join(self.temp_dir, "test_dup.db")
        self.db = DatabaseManager(self.db_path)
        self.scanner = DirectoryScanner(self.db)
        self.detector = DuplicateDetector(self.db)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_05_exact_duplicate_detection_differing_filenames(self):
        """Test 5: Detect exact duplicate files even when filenames/paths differ."""
        sub1 = os.path.join(self.temp_dir, "folder_one")
        sub2 = os.path.join(self.temp_dir, "folder_two")
        os.makedirs(sub1, exist_ok=True)
        os.makedirs(sub2, exist_ok=True)

        content = b"Exact identical binary and text payload for test 5" * 20
        path_a = os.path.join(sub1, "original_report.txt")
        path_b = os.path.join(sub2, "cloned_backup_data.log")  # Different name & extension

        with open(path_a, "wb") as fa, open(path_b, "wb") as fb:
            fa.write(content)
            fb.write(content)

        # Scan folder
        self.scanner.scan_directory(self.temp_dir)

        # Run duplicate detection
        result = self.detector.detect_duplicates(verify_bytes=True)

        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["total_groups"], 1)
        self.assertEqual(result["total_redundant_copies"], 1)

        group = result["groups"][0]
        self.assertEqual(group["file_count"], 2)
        self.assertEqual(group["file_size"], len(content))
        self.assertEqual(group["reclaimable_size"], len(content))  # (2 - 1) * S

        group_paths = {f["path"] for f in group["files"]}
        self.assertEqual(group_paths, {os.path.normpath(path_a), os.path.normpath(path_b)})

    def test_06_rejection_of_same_sized_files_with_different_content(self):
        """Test 6: Files of identical size but different contents MUST NOT be flagged as duplicates."""
        folder = os.path.join(self.temp_dir, "false_positives")
        os.makedirs(folder, exist_ok=True)

        # Both exactly 512 bytes, completely different contents
        data_a = b"A" * 512
        data_b = b"B" * 512

        path_a = os.path.join(folder, "payload_a.dat")
        path_b = os.path.join(folder, "payload_b.dat")

        with open(path_a, "wb") as fa, open(path_b, "wb") as fb:
            fa.write(data_a)
            fb.write(data_b)

        self.scanner.scan_directory(self.temp_dir)
        result = self.detector.detect_duplicates(verify_bytes=True)

        # SHA-256 and byte check must separate these
        self.assertEqual(result["total_groups"], 0)
        self.assertEqual(result["total_redundant_copies"], 0)
        self.assertEqual(result["total_reclaimable_bytes"], 0)

    def test_07_handling_of_empty_files(self):
        """Test 7: Handle 0-byte empty files correctly without crashing."""
        folder = os.path.join(self.temp_dir, "empty_files")
        os.makedirs(folder, exist_ok=True)

        empty_1 = os.path.join(folder, "empty1.txt")
        empty_2 = os.path.join(folder, "empty2.txt")
        empty_3 = os.path.join(folder, "empty3.txt")

        for p in (empty_1, empty_2, empty_3):
            with open(p, "wb") as f:
                pass

        self.scanner.scan_directory(self.temp_dir)
        result = self.detector.detect_duplicates(verify_bytes=True)

        self.assertEqual(result["total_groups"], 1)
        group = result["groups"][0]
        self.assertEqual(group["file_count"], 3)
        self.assertEqual(group["file_size"], 0)
        self.assertEqual(group["reclaimable_size"], 0)  # (3 - 1) * 0 = 0


if __name__ == "__main__":
    unittest.main()
