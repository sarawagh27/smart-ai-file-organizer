"""
utils.py
--------
Shared utility helpers used across the project:
  - Logging setup
  - Safe file move with rename-on-collision
  - Category folder creation
  - Simple stats printer
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict

# Supported file extensions the organizer will process
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# All category folder names
CATEGORIES = ["Finance", "Resume", "AI", "Research", "Personal", "Other"]


def setup_logging(log_dir: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logger to write to both the console and a rotating log file.

    Parameters
    ----------
    log_dir : directory where organizer.log will be created
    level   : logging level (default INFO)

    Returns
    -------
    The root logger instance.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "organizer.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid adding duplicate handlers on repeated calls
    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)
    else:
        root.handlers.clear()
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    logging.info("Logging initialised → %s", log_path)
    return root


def create_category_folders(base_dir: str) -> None:
    """
    Create one sub-folder per category inside base_dir (if not already present).
    """
    for category in CATEGORIES:
        folder = Path(base_dir) / category
        folder.mkdir(parents=True, exist_ok=True)
    logging.getLogger(__name__).info(
        "Category folders ensured under '%s'.", base_dir
    )


def safe_move(src: str, dest_dir: str) -> str:
    """
    Move *src* into *dest_dir*.

    If a file with the same name already exists in dest_dir, append an
    incrementing counter to avoid overwriting:  file.pdf → file_1.pdf → file_2.pdf

    Returns
    -------
    The final destination path as a string.
    """
    logger = logging.getLogger(__name__)
    src_path = Path(src)
    dest_path = Path(dest_dir) / src_path.name

    # Resolve name collision
    counter = 1
    while dest_path.exists():
        dest_path = Path(dest_dir) / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1

    shutil.move(str(src_path), str(dest_path))
    logger.info("Moved '%s' → '%s'", src_path.name, dest_path)
    return str(dest_path)


def scan_directory(directory: str) -> list[str]:
    """
    Return a list of absolute file paths for all supported files in *directory*
    (non-recursive — only the top level).
    """
    result = []
    base = Path(directory)
    if not base.is_dir():
        logging.getLogger(__name__).error("'%s' is not a valid directory.", directory)
        return result

    for entry in base.iterdir():
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            result.append(str(entry.resolve()))

    logging.getLogger(__name__).info(
        "Found %d supported file(s) in '%s'.", len(result), directory
    )
    return result


def print_summary(stats: Dict) -> None:
    """
    Print a formatted summary table to stdout.

    Expected keys in stats:
        total_files, processed, moved, duplicates, errors, by_category
    """
    width = 44
    line = "─" * width
    print(f"\n{'━' * width}")
    print(f"  {'Smart AI File Organizer — Summary':^{width - 4}}")
    print(f"{'━' * width}")
    print(f"  Total files found   : {stats.get('total_files', 0)}")
    print(f"  Successfully moved  : {stats.get('moved', 0)}")
    print(f"  Duplicates skipped  : {stats.get('duplicates', 0)}")
    print(f"  Errors              : {stats.get('errors', 0)}")
    print(f"  {line}")
    print(f"  {'Category':<20} {'Files':>6}")
    print(f"  {line}")
    for cat, count in sorted(stats.get("by_category", {}).items()):
        print(f"  {cat:<20} {count:>6}")
    print(f"{'━' * width}\n")
