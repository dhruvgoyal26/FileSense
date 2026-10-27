"""
FileSense — High-Performance Local File Indexing and Redundancy Detection Tool
DSA-II (CCSE0301) Final PBL Submission

Main entry point.
"""

import sys
import argparse
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import APP_NAME, APP_VERSION
from ui.main_window import MainWindow
from scripts.generate_demo_data import generate_demo_dataset


def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--demo", action="store_true", help="Generate demo dataset before launching")
    parser.add_argument("--scan", type=str, help="Initial directory path to open/scan")
    parser.add_argument("--test", action="store_true", help="Run automated test suite and exit")
    parser.add_argument("--db", type=str, help="Custom SQLite database file path")
    args = parser.parse_args()

    if args.test:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    if args.demo:
        demo_path = generate_demo_dataset()
        if not args.scan:
            args.scan = demo_path

    # Launch GUI
    app = MainWindow(db_path=args.db)

    if args.scan and os.path.isdir(args.scan):
        app.current_root_path = os.path.normpath(args.scan)
        app.lbl_active_root.config(text=app.current_root_path)
        app.after(500, app.start_scan_thread)

    app.mainloop()


if __name__ == "__main__":
    main()
