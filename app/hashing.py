"""
Streaming chunked hashing and byte verification module.
Avoids memory exhaustion by processing in 1 MiB blocks.
Ensures file integrity and collision-proof duplicate detection.
"""

import hashlib
import os
from typing import Optional, Tuple
from app.config import HASH_CHUNK_SIZE, HASH_ALGORITHM


class HashingError(Exception):
    """Exception raised for errors during file hashing."""
    pass


def calculate_file_hash(
    file_path: str,
    chunk_size: int = HASH_CHUNK_SIZE,
    verify_stability: bool = True,
) -> Tuple[Optional[str], str]:
    """
    Compute SHA-256 hash using chunked streaming reads.
    
    Returns:
        (hash_hex_str, status_str):
        hash_hex_str: hex digest or None if error/instability occurred
        status_str: 'SUCCESS', 'PERMISSION_ERROR', 'NOT_FOUND', 'CHANGED_DURING_HASH', 'READ_ERROR'
    """
    if not os.path.exists(file_path):
        return None, "NOT_FOUND"

    try:
        stat_before = os.stat(file_path)
    except (PermissionError, OSError) as e:
        return None, f"STAT_ERROR: {e}"

    # Empty file has well-known SHA-256
    if stat_before.st_size == 0:
        empty_hash = hashlib.sha256(b"").hexdigest()
        return empty_hash, "SUCCESS"

    hasher = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
    except PermissionError:
        return None, "PERMISSION_ERROR"
    except (FileNotFoundError, OSError) as e:
        return None, f"READ_ERROR: {e}"

    if verify_stability:
        try:
            stat_after = os.stat(file_path)
            if (
                stat_after.st_size != stat_before.st_size
                or stat_after.st_mtime != stat_before.st_mtime
            ):
                return None, "CHANGED_DURING_HASH"
        except OSError:
            return None, "CHANGED_DURING_HASH"

    return hasher.hexdigest(), "SUCCESS"


def verify_identical_bytes(
    path_a: str,
    path_b: str,
    chunk_size: int = HASH_CHUNK_SIZE,
) -> bool:
    """
    Perform byte-for-byte verification between two candidate files.
    Used in Stage 3 duplicate verification for absolute certainty.
    """
    if path_a == path_b:
        return True

    try:
        size_a = os.path.getsize(path_a)
        size_b = os.path.getsize(path_b)
        if size_a != size_b:
            return False

        if size_a == 0:
            return True

        with open(path_a, "rb") as f_a, open(path_b, "rb") as f_b:
            while True:
                chunk_a = f_a.read(chunk_size)
                chunk_b = f_b.read(chunk_size)
                if chunk_a != chunk_b:
                    return False
                if not chunk_a:
                    break
        return True
    except (OSError, PermissionError):
        return False
