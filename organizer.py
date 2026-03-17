"""
organizer.py
------------
Orchestrates the full file-organising pipeline:

  1. Scan directory (optionally recursive) for supported files
  2. Check for duplicates — skip if found
  3. Extract text from each file
  4. Classify text into a category
  5. Move file (or simulate in dry-run mode)
  6. Return run statistics
"""

import logging
from pathlib import Path
from typing import Dict

from classifier import DocumentClassifier
from duplicate_detector import DuplicateDetector
from text_extractor import extract_text
from utils import (
    CATEGORIES,
    create_category_folders,
    safe_move,
    scan_directory,
)

logger = logging.getLogger(__name__)


class FileOrganizer:
    """
    High-level controller for the Smart AI File Organizer.

    Parameters
    ----------
    target_dir : str   — folder to scan and organise
    dry_run    : bool  — if True, simulate without moving files
    recursive  : bool  — if True, scan sub-folders too
    """

    def __init__(self, target_dir: str, dry_run: bool = False, recursive: bool = False):
        self.target_dir = str(Path(target_dir).resolve())
        self.dry_run   = dry_run
        self.recursive = recursive
        self.classifier        = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()

        self._stats: Dict = {
            "total_files": 0,
            "moved":       0,
            "duplicates":  0,
            "errors":      0,
            "by_category": {cat: 0 for cat in self.classifier.categories},
        }

    # ── public ──────────────────────────────────────────────────────────────
    def run(self) -> Dict:
        mode = "DRY RUN" if self.dry_run else "LIVE"
        sep  = "=" * 60

        logger.info(sep)
        logger.info("Smart AI File Organizer — %s MODE", mode)
        logger.info("Target    : %s", self.target_dir)
        logger.info("Recursive : %s", self.recursive)
        logger.info(sep)

        if self.dry_run:
            logger.info("*** DRY RUN: No files will be moved ***")

        logger.info("Training document classifier…")
        self.classifier.train()

        if not self.dry_run:
            create_category_folders(self.target_dir, self.classifier.categories)

        files = scan_directory(self.target_dir, recursive=self.recursive)
        self._stats["total_files"] = len(files)

        if not files:
            logger.warning("No supported files found. Nothing to do.")
            return self._stats

        for filepath in files:
            self._process_file(filepath)

        logger.info(sep)
        logger.info(
            "Run complete (%s). Moved: %d | Duplicates: %d | Errors: %d",
            mode, self._stats["moved"], self._stats["duplicates"], self._stats["errors"],
        )
        logger.info(sep)
        return self._stats

    # ── internal ────────────────────────────────────────────────────────────
    def _process_file(self, filepath: str) -> None:
        filename = Path(filepath).name
        logger.info("Processing: %s", filename)

        # Duplicate check
        is_dup, original = self.duplicate_detector.check(filepath)
        if is_dup:
            logger.warning(
                "DUPLICATE — skipping '%s' (matches '%s')",
                filename, Path(original).name,
            )
            self._stats["duplicates"] += 1
            return

        # Text extraction
        try:
            text = extract_text(filepath)
        except Exception as exc:
            logger.error("Extraction error for '%s': %s", filename, exc)
            self._stats["errors"] += 1
            return

        if not text.strip():
            logger.warning("No text extracted from '%s'; classifying as 'Other'.", filename)

        # Classification
        try:
            category = self.classifier.predict(text)
        except Exception as exc:
            logger.error("Classification error for '%s': %s", filename, exc)
            category = "Other"

        logger.info("  ↳ Category: %s", category)
        dest_dir = str(Path(self.target_dir) / category)

        # Move or simulate
        if self.dry_run:
            logger.info("  [DRY RUN] '%s' → %s/", filename, category)
        else:
            try:
                safe_move(filepath, dest_dir)
            except Exception as exc:
                logger.error("Move failed for '%s': %s", filename, exc)
                self._stats["errors"] += 1
                return

        self._stats["moved"] += 1
        self._stats["by_category"][category] = (
            self._stats["by_category"].get(category, 0) + 1
        )
