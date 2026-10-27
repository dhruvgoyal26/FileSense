"""
Tests for Hash Table In-Memory Indexes and SQLite Database Persistence.
Covers Requirements:
3. Filename, extension, and size indexes
4. Persistence and retrieval from SQLite
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from app.database import DatabaseManager
from app.file_index import FileIndex


class TestIndexAndDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="filesense_idx_test_")
        self.db_path = os.path.join(self.temp_dir, "test_index.db")
        self.db = DatabaseManager(self.db_path)
        self.index = FileIndex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_03_in_memory_hash_table_indexing(self):
        """Test 3: Filename, extension, and size indexes."""
        mock_records = [
            {
                "id": 1,
                "filename": "Report.pdf",
                "path": "/docs/Report.pdf",
                "extension": ".pdf",
                "size": 1024,
                "type": "Document",
                "content_hash": "hash_aaa",
            },
            {
                "id": 2,
                "filename": "Summary.pdf",
                "path": "/docs/Summary.pdf",
                "extension": ".pdf",
                "size": 2048,
                "type": "Document",
                "content_hash": "hash_bbb",
            },
            {
                "id": 3,
                "filename": "Chart.png",
                "path": "/images/Chart.png",
                "extension": ".png",
                "size": 1024,
                "type": "Image",
                "content_hash": "hash_ccc",
            },
        ]

        self.index.load_from_records(mock_records)

        # 1. Exact filename lookup O(1)
        res_fn = self.index.search_exact_filename("Report.pdf")
        self.assertEqual(len(res_fn), 1)
        self.assertEqual(res_fn[0]["id"], 1)

        # Case insensitive check
        res_fn_lower = self.index.search_exact_filename("report.pdf")
        self.assertEqual(len(res_fn_lower), 1)

        # 2. Extension lookup O(1)
        res_ext = self.index.search_exact_extension(".pdf")
        self.assertEqual(len(res_ext), 2)
        pdf_ids = {r["id"] for r in res_ext}
        self.assertEqual(pdf_ids, {1, 2})

        # 3. Size index lookup O(1)
        res_sz = self.index.search_exact_size(1024)
        self.assertEqual(len(res_sz), 2)
        sz_ids = {r["id"] for r in res_sz}
        self.assertEqual(sz_ids, {1, 3})

        # 4. Multi-criteria compound search
        multi_res = self.index.multi_criteria_search(
            query="chart",
            extension=".png",
            category="Image",
            min_size=500,
            max_size=1500,
        )
        self.assertEqual(len(multi_res), 1)
        self.assertEqual(multi_res[0]["filename"], "Chart.png")

    def test_04_sqlite_persistence_and_retrieval(self):
        """Test 4: Persistence and retrieval from SQLite."""
        # Insert folder
        folder_id = self.db.upsert_folder("documents", "/var/documents")
        self.assertGreater(folder_id, 0)

        # Insert file
        file_id = self.db.upsert_file({
            "parent_id": folder_id,
            "filename": "thesis.docx",
            "path": "/var/documents/thesis.docx",
            "type": "Document",
            "extension": ".docx",
            "size": 45000,
            "created_at": "2026-10-27T10:00:00",
            "modified_at": "2026-10-27T10:30:00",
            "content_hash": "thesis_hash_xyz",
            "hash_status": "SUCCESS",
        })
        self.assertGreater(file_id, 0)

        # Retrieve file
        fetched = self.db.get_file_by_id(file_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["filename"], "thesis.docx")
        self.assertEqual(fetched["size"], 45000)
        self.assertEqual(fetched["content_hash"], "thesis_hash_xyz")

        # Test scan history logging
        scan_id = self.db.record_scan_start("/var/documents")
        self.db.record_scan_completion(
            scan_id=scan_id,
            files_scanned=10,
            folders_scanned=2,
            bytes_scanned=500000,
            status="COMPLETED",
            error_count=0,
        )
        history = self.db.get_scan_history(limit=5)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "COMPLETED")
        self.assertEqual(history[0]["files_scanned"], 10)


if __name__ == "__main__":
    unittest.main()
