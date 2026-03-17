"""
utils.py
--------
Shared utility helpers:
  - Logging setup
  - Safe file move with rename-on-collision
  - Category folder creation
  - Directory scanner (with optional recursion)
  - Summary printer
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CONFIG = Path(__file__).parent / "config.json"


def _load_config() -> dict:
    try:
        with open(DEFAULT_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_cfg = _load_config()
SUPPORTED_EXTENSIONS = set(
    _cfg.get("organizer", {}).get(
        "supported_extensions",
        [".pdf", ".txt", ".docx", ".xlsx", ".pptx", ".csv", ".png", ".jpg", ".jpeg"],
    )
)
CATEGORIES = _cfg.get(
    "categories",
    ["Finance", "Resume", "AI", "Research", "Personal", "Legal", "Medical", "Other"],
)


def setup_logging(log_dir: str, level: int = logging.INFO) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "organizer.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.info("Logging initialised → %s", log_path)
    return root


def create_category_folders(base_dir: str, categories: Optional[List[str]] = None) -> None:
    cats = categories or CATEGORIES
    for category in cats:
        (Path(base_dir) / category).mkdir(parents=True, exist_ok=True)
    logging.getLogger(__name__).info("Category folders ensured under '%s'.", base_dir)


def safe_move(src: str, dest_dir: str) -> str:
    """Move src into dest_dir; appends counter on name collision."""
    logger = logging.getLogger(__name__)
    src_path = Path(src)
    dest_path = Path(dest_dir) / src_path.name

    counter = 1
    while dest_path.exists():
        dest_path = Path(dest_dir) / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1

    shutil.move(str(src_path), str(dest_path))
    logger.info("Moved '%s' → '%s'", src_path.name, dest_path)
    return str(dest_path)


def scan_directory(directory: str, recursive: bool = False) -> List[str]:
    """
    Return absolute paths of all supported files in directory.

    Parameters
    ----------
    directory : str   — folder to scan
    recursive : bool  — if True, also scan all sub-folders
    """
    result = []
    base = Path(directory)

    if not base.is_dir():
        logging.getLogger(__name__).error("'%s' is not a valid directory.", directory)
        return result

    # Use rglob for recursive, iterdir for top-level only
    entries = base.rglob("*") if recursive else base.iterdir()

    for entry in entries:
        # Skip category sub-folders to avoid re-processing already-moved files
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            # Skip files already inside a category sub-folder
            try:
                relative = entry.relative_to(base)
                parts = relative.parts
                if len(parts) > 1 and parts[0] in CATEGORIES:
                    continue
            except ValueError:
                pass
            result.append(str(entry.resolve()))

    logging.getLogger(__name__).info(
        "Found %d supported file(s) in '%s' (recursive=%s).",
        len(result), directory, recursive,
    )
    return result


def print_summary(stats: Dict, dry_run: bool = False) -> None:
    width = 46
    print(f"\n{'━' * width}")
    print(f"  {'Smart AI File Organizer — Summary':^{width - 4}}")
    if dry_run:
        print(f"\033[93m  *** DRY RUN — no files were moved ***\033[0m")
    print(f"{'━' * width}")
    print(f"  Total files found   : {stats.get('total_files', 0)}")
    label = "Would move" if dry_run else "Successfully moved"
    print(f"  {label:<20}: {stats.get('moved', 0)}")
    print(f"  Duplicates skipped  : {stats.get('duplicates', 0)}")
    print(f"  Errors              : {stats.get('errors', 0)}")
    print(f"  {'─' * (width - 2)}")
    print(f"  {'Category':<22} {'Files':>6}")
    print(f"  {'─' * (width - 2)}")
    for cat, count in sorted(stats.get("by_category", {}).items()):
        print(f"  {cat:<22} {count:>6}")
    print(f"{'━' * width}\n")
