"""
Empirical Performance Benchmarking Module.
Compares in-memory hash table indexed queries against raw filesystem traversal.
DSA Concept: Hash table O(1) avg lookup vs Unindexed disk traversal O(N).
"""

import os
import time
from typing import Dict, Any, List
from app.file_index import FileIndex


def benchmark_search_comparison(
    root_path: str,
    file_index: FileIndex,
    query_str: str,
) -> Dict[str, Any]:
    """
    Run identical search query using:
    1. FileSense In-Memory Hash Index
    2. Raw Filesystem Walk (baseline disk I/O)
    
    Measures actual elapsed time without fabrication.
    """
    clean_query = query_str.strip().lower()

    # 1. Benchmark: In-Memory Index Search
    t0 = time.perf_counter()
    indexed_results = file_index.multi_criteria_search(query=clean_query)
    indexed_elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Benchmark: Raw Baseline Directory Walk
    t1 = time.perf_counter()
    raw_results: List[str] = []
    disk_scanned_files = 0

    if os.path.isdir(root_path):
        for dirpath, _, filenames in os.walk(root_path):
            for fn in filenames:
                disk_scanned_files += 1
                if clean_query in fn.lower():
                    raw_results.append(os.path.join(dirpath, fn))

    raw_elapsed_ms = (time.perf_counter() - t1) * 1000.0

    # Compute actual speedup factor
    if indexed_elapsed_ms > 0:
        speedup = raw_elapsed_ms / indexed_elapsed_ms
    else:
        speedup = 1.0

    return {
        "query": query_str,
        "root_path": root_path,
        "indexed_match_count": len(indexed_results),
        "indexed_time_ms": indexed_elapsed_ms,
        "raw_match_count": len(raw_results),
        "raw_scanned_files": disk_scanned_files,
        "raw_time_ms": raw_elapsed_ms,
        "speedup_factor": speedup,
        "explanation": (
            f"In-memory hash index completed in {indexed_elapsed_ms:.3f} ms. "
            f"Raw filesystem walk traversed {disk_scanned_files} files in {raw_elapsed_ms:.3f} ms. "
            f"Speedup depends on dataset size, OS disk caching, and storage medium."
        ),
    }
