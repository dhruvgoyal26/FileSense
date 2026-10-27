"""
Safe Demonstration Dataset Generator for FileSense.
Generates synthetic files, directories, exact byte duplicates, identical-size distinct files,
and multi-copy clusters for testing and PBL demonstration.
"""

import os
import sys
from typing import Optional
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_demo_dataset(target_dir: Optional[str] = None) -> str:
    """
    Generate synthetic folder hierarchy with known duplicates and edge cases.
    """
    base_dir = Path(target_dir or (PROJECT_ROOT / "demo_data"))
    base_dir.mkdir(parents=True, exist_ok=True)

    # Subdirectories
    folders = [
        base_dir / "documents",
        base_dir / "images",
        base_dir / "backups",
        base_dir / "reports",
        base_dir / "code",
        base_dir / "data",
        base_dir / "nested" / "archive",
    ]
    for f in folders:
        f.mkdir(parents=True, exist_ok=True)

    # ==========================================================
    # 1. Exact Duplicate Pair 1 (Notes)
    # ==========================================================
    notes_content = (
        "FileSense Project Notes - CCSE0301 DSA-II\n"
        "Key concepts: Hash-table indexing, Adjacency list graph, DFS/BFS components,\n"
        "Dynamic programming (0/1 Knapsack, LCS, Matrix Chain Multiplication).\n"
        "This is an exact duplicate file designed for PBL evaluation.\n"
    ).encode("utf-8")

    (base_dir / "documents" / "notes.txt").write_bytes(notes_content)
    (base_dir / "backups" / "notes_copy.txt").write_bytes(notes_content)

    # ==========================================================
    # 2. Exact Duplicate Pair 2 (Assignment Proposal)
    # ==========================================================
    proposal_content = (
        "Project Proposal: Local File Intelligence & Redundancy Detection\n"
        "Student PBL Submission for DSA-II Course CCSE0301.\n"
        "Objective: Minimize redundant disk I/O through persistent indexing and graph clustering.\n"
        "All algorithms verified on empirical data.\n"
    ).encode("utf-8") * 5

    (base_dir / "documents" / "assignment.txt").write_bytes(proposal_content)
    (base_dir / "backups" / "assignment_backup.txt").write_bytes(proposal_content)

    # ==========================================================
    # 3. Exact Triplicate Group (Sensor CSV Data) - 3 identical copies!
    # ==========================================================
    csv_lines = ["timestamp,sensor_id,temperature,humidity,status\n"]
    for i in range(100):
        csv_lines.append(f"2026-10-27T10:{i%60:02d}:00,SENS_{i%5},24.{i%10},55.{i%8},NORMAL\n")
    csv_content = "".join(csv_lines).encode("utf-8")

    (base_dir / "data" / "sensor_readings.csv").write_bytes(csv_content)
    (base_dir / "backups" / "sensor_readings_2026.csv").write_bytes(csv_content)
    (base_dir / "reports" / "raw_sensor_data.csv").write_bytes(csv_content)

    # ==========================================================
    # 4. Exact Duplicate Code Files
    # ==========================================================
    py_code = (
        "# Utility script for algorithms\n"
        "def compute_hash(val):\n"
        "    return hash(val) & 0xFFFFFFFF\n\n"
        "if __name__ == '__main__':\n"
        "    print('DSA-II PBL utility active')\n"
    ).encode("utf-8")

    (base_dir / "code" / "algorithm_utils.py").write_bytes(py_code)
    (base_dir / "backups" / "algorithm_utils_v1.py").write_bytes(py_code)

    # ==========================================================
    # 5. Same Size (1024 bytes) but DIFFERENT Content (False match check)
    # Tests that Stage 1 size grouping correctly filters to Stage 2,
    # where SHA-256 rejects them!
    # ==========================================================
    buffer_a = b"A" * 1024
    buffer_b = b"B" * 1024
    (base_dir / "documents" / "same_size_file_A.dat").write_bytes(buffer_a)
    (base_dir / "reports" / "same_size_file_B.dat").write_bytes(buffer_b)

    # ==========================================================
    # 6. Empty Files (0 bytes duplicate pair)
    # ==========================================================
    (base_dir / "backups" / "empty_log_1.log").write_bytes(b"")
    (base_dir / "reports" / "empty_log_2.log").write_bytes(b"")

    # ==========================================================
    # 7. Unique Files of Various Categories and Sizes
    # ==========================================================
    (base_dir / "reports" / "quarterly_summary.pdf").write_bytes(b"%PDF-1.4 Minimal PDF synthetic header data\n" * 40)
    (base_dir / "code" / "main_engine.py").write_bytes(b"print('Main Engine Execution')\n" * 15)
    (base_dir / "documents" / "research_paper.md").write_bytes(b"# Research Paper Markdown\nEmpirical evaluation.\n" * 20)
    (base_dir / "nested" / "archive" / "compressed_archive.zip").write_bytes(b"PK\x03\x04Synthetic zip archive bytes" * 50)

    # Simple synthetic PNG header bytes
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00" + (b"\x00" * 200)
    (base_dir / "images" / "system_diagram.png").write_bytes(png_bytes)

    print(f"Demo dataset successfully generated at: {base_dir}")
    return str(base_dir)


if __name__ == "__main__":
    generate_demo_dataset()
