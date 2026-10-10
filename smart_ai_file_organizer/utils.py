"""Shared utility helpers for logging, scanning, moves, and summaries."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import ConfigError, load_config


def _load_config() -> dict:
    try:
        return load_config()
    except ConfigError:
        return {}


_cfg = _load_config()
DEFAULT_EXTENSIONS = [
    ".pdf", ".txt", ".docx", ".xlsx", ".pptx", ".csv",
    ".eml", ".msg", ".zip", ".png", ".jpg", ".jpeg",
]
DEFAULT_DUPLICATES_FOLDER = "_Duplicates"

# Module-level defaults (read once from the default config). Callers that use a
# custom --config should pass their own values to scan_directory() instead.
SUPPORTED_EXTENSIONS = set(
    _cfg.get("organizer", {}).get("supported_extensions", DEFAULT_EXTENSIONS)
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

    logging.info("Logging initialised -> %s", log_path)
    return root


def create_category_folders(base_dir: str, categories: Optional[List[str]] = None) -> None:
    cats = categories or CATEGORIES
    for category in cats:
        (Path(base_dir) / category).mkdir(parents=True, exist_ok=True)
    logging.getLogger(__name__).info("Category folders ensured under '%s'.", base_dir)


def unique_path(directory: Path, filename: str) -> Path:
    """Return directory/filename, adding _1, _2… until the path is unused."""
    candidate = directory / filename
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def safe_move(src: str, dest_dir: str, dest_name: Optional[str] = None) -> str:
    """
    Move src into dest_dir, never overwriting an existing file.

    ``dest_name`` lets a rename and a move happen as one atomic step; the
    original name is kept when it is omitted. A counter is appended on collision.
    """
    logger = logging.getLogger(__name__)
    src_path = Path(src)
    dest_root = Path(dest_dir)
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_path = unique_path(dest_root, dest_name or src_path.name)

    shutil.move(str(src_path), str(dest_path))
    logger.info("Moved '%s' -> '%s'", src_path.name, dest_path)
    return str(dest_path)


def scan_directory(
    directory: str,
    recursive: bool = False,
    categories: Optional[Iterable[str]] = None,
    extensions: Optional[Iterable[str]] = None,
    skip_folders: Iterable[str] = (),
) -> List[str]:
    """
    Return absolute paths of supported files in ``directory``.

    Files already inside a category folder (or any ``skip_folders`` entry such
    as the duplicates folder) are ignored, and so are hidden folders like
    ``.git`` or ``.smart-organizer``. ``categories`` and ``extensions`` default
    to the module-level values from the default config; pass the active
    config's values when using ``--config``.
    """
    result = []
    base = Path(directory)

    if not base.is_dir():
        logging.getLogger(__name__).error("'%s' is not a valid directory.", directory)
        return result

    skip = set(categories if categories is not None else CATEGORIES) | set(skip_folders)
    exts = {e.lower() for e in (extensions if extensions is not None else SUPPORTED_EXTENSIONS)}

    entries = base.rglob("*") if recursive else base.iterdir()

    for entry in entries:
        if not entry.is_file() or entry.suffix.lower() not in exts:
            continue
        try:
            parts = entry.relative_to(base).parts
        except ValueError:
            parts = (entry.name,)
        folders = parts[:-1]
        if folders and (folders[0] in skip or any(p.startswith(".") for p in folders)):
            continue
        result.append(str(entry.resolve()))

    logging.getLogger(__name__).info(
        "Found %d supported file(s) in '%s' (recursive=%s).",
        len(result), directory, recursive,
    )
    return result


def print_summary(stats: Dict, dry_run: bool = False) -> None:
    width = 46
    print(f"\n{'=' * width}")
    print(f"  {'Smart AI File Organizer - Summary':^{width - 4}}")
    if dry_run:
        print("  *** DRY RUN - no files were moved ***")
    print(f"{'=' * width}")
    print(f"  Total files found   : {stats.get('total_files', 0)}")
    label = "Would move" if dry_run else "Successfully moved"
    print(f"  {label:<20}: {stats.get('moved', 0)}")
    print(f"  Duplicates found    : {stats.get('duplicates', 0)}")
    print(f"  Errors              : {stats.get('errors', 0)}")
    print(f"  {'-' * (width - 2)}")
    print(f"  {'Category':<22} {'Files':>6}")
    print(f"  {'-' * (width - 2)}")
    for cat, count in sorted(stats.get("by_category", {}).items()):
        print(f"  {cat:<22} {count:>6}")
    print(f"{'=' * width}\n")
