"""
Configuration and constants for FileSense application.
"""

from pathlib import Path
import os

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directory and default SQLite database path
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "filesense.db"

# Application Metadata
APP_NAME = "FileSense — Local File Intelligence"
APP_VERSION = "1.0.0"
COURSE_NAME = "Data Structures and Algorithms-II"
COURSE_CODE = "CCSE0301"
SDG_ALIGNMENT = "SDG 9: Industry, Innovation and Infrastructure"

# File Hashing Configuration
HASH_ALGORITHM = "sha256"
HASH_CHUNK_SIZE = 1024 * 1024  # 1 MiB chunk reads

# Scanner Exclusions (Files and folders to skip by default)
DEFAULT_EXCLUDED_NAMES = {
    "filesense.db",
    "filesense.db-journal",
    "filesense.db-wal",
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    ".system_generated",
    ".gemini",
    "node_modules",
    "$RECYCLE.BIN",
    "System Volume Information",
}

DEFAULT_EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".tmp",
    ".bak",
    ".swp",
}

# File Categories based on extensions
EXTENSION_CATEGORIES = {
    # Documents
    ".pdf": "Document",
    ".doc": "Document",
    ".docx": "Document",
    ".txt": "Document",
    ".rtf": "Document",
    ".odt": "Document",
    ".xlsx": "Document",
    ".xls": "Document",
    ".csv": "Document",
    ".pptx": "Document",
    ".ppt": "Document",
    ".md": "Document",
    ".tex": "Document",
    # Images
    ".jpg": "Image",
    ".jpeg": "Image",
    ".png": "Image",
    ".gif": "Image",
    ".bmp": "Image",
    ".webp": "Image",
    ".svg": "Image",
    ".ico": "Image",
    ".tiff": "Image",
    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".ogg": "Audio",
    ".m4a": "Audio",
    # Video
    ".mp4": "Video",
    ".mkv": "Video",
    ".avi": "Video",
    ".mov": "Video",
    ".wmv": "Video",
    ".flv": "Video",
    ".webm": "Video",
    # Archives
    ".zip": "Archive",
    ".rar": "Archive",
    ".7z": "Archive",
    ".tar": "Archive",
    ".gz": "Archive",
    ".bz2": "Archive",
    # Code
    ".py": "Code",
    ".java": "Code",
    ".c": "Code",
    ".cpp": "Code",
    ".h": "Code",
    ".hpp": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".html": "Code",
    ".css": "Code",
    ".json": "Code",
    ".xml": "Code",
    ".sql": "Code",
    ".rs": "Code",
    ".go": "Code",
    ".sh": "Code",
    ".bat": "Code",
    ".ps1": "Code",
}


def get_file_category(extension: str) -> str:
    """Return categorized type for a file extension."""
    if not extension:
        return "Unknown"
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    return EXTENSION_CATEGORIES.get(ext, "Other")


def format_bytes(bytes_count: int | float) -> str:
    """Format bytes into human-readable string (B, KB, MB, GB, TB)."""
    if bytes_count < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    val = float(bytes_count)
    while val >= 1024.0 and unit_index < len(units) - 1:
        val /= 1024.0
        unit_index += 1
    if unit_index == 0:
        return f"{int(val)} B"
    return f"{val:.2f} {units[unit_index]}"
