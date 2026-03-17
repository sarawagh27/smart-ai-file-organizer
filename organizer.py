"""
organizer.py
------------
Orchestrates the full file-organising pipeline:

  1. Scan directory for supported files
  2. Check for duplicates (skip if found)
  3. Extract text from each file
  4. Classify the text into a category
  5. Move the file into the matching category folder
  6. Collect and return run statistics
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
    target_dir : str
        The folder to scan and organise.
    """

    def __init__(self, target_dir: str):
        self.target_dir = str(Path(target_dir).resolve())
        self.classifier = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()

        # Runtime statistics
        self._stats: Dict = {
            "total_files": 0,
            "moved": 0,
            "duplicates": 0,
            "errors": 0,
            "by_category": {cat: 0 for cat in CATEGORIES},
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict:
        """
        Execute the complete organise pipeline.

        Returns
        -------
        dict with keys: total_files, moved, duplicates, errors, by_category
        """
        logger.info("=" * 60)
        logger.info("Starting Smart AI File Organizer on '%s'", self.target_dir)
        logger.info("=" * 60)

        # Step 1 — train classifier
        logger.info("Training document classifier…")
        self.classifier.train()

        # Step 2 — create category sub-folders
        create_category_folders(self.target_dir)

        # Step 3 — scan for files
        files = scan_directory(self.target_dir)
        self._stats["total_files"] = len(files)

        if not files:
            logger.warning("No supported files found. Nothing to do.")
            return self._stats

        # Step 4 — process each file
        for filepath in files:
            self._process_file(filepath)

        logger.info("=" * 60)
        logger.info("Run complete. Moved: %d | Duplicates: %d | Errors: %d",
                    self._stats["moved"],
                    self._stats["duplicates"],
                    self._stats["errors"])
        logger.info("=" * 60)

        return self._stats

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_file(self, filepath: str) -> None:
        """Process a single file: dedup → extract → classify → move."""
        filename = Path(filepath).name
        logger.info("Processing: %s", filename)

        # --- Duplicate check ---
        is_dup, original = self.duplicate_detector.check(filepath)
        if is_dup:
            logger.warning(
                "DUPLICATE — skipping '%s' (same content as '%s')",
                filename, Path(original).name,
            )
            self._stats["duplicates"] += 1
            return

        # --- Text extraction ---
        try:
            text = extract_text(filepath)
        except Exception as exc:
            logger.error("Text extraction error for '%s': %s", filename, exc)
            self._stats["errors"] += 1
            return

        if not text.strip():
            logger.warning("No text extracted from '%s'; classifying as 'Other'.", filename)

        # --- Classification ---
        try:
            category = self.classifier.predict(text)
        except Exception as exc:
            logger.error("Classification error for '%s': %s", filename, exc)
            category = "Other"

        logger.info("  ↳ Category: %s", category)

        # --- Move file ---
        dest_dir = str(Path(self.target_dir) / category)
        try:
            safe_move(filepath, dest_dir)
            self._stats["moved"] += 1
            self._stats["by_category"][category] += 1
        except Exception as exc:
            logger.error("Failed to move '%s': %s", filename, exc)
            self._stats["errors"] += 1
