"""
organizer.py
------------
Orchestrates the full file-organising pipeline.

Level 1 additions:
  - Records confidence score for every file
  - Flags low-confidence files in stats and log
  - Stores file→text map so GUI can offer manual override
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from classifier import DocumentClassifier
from renamer import SmartRenamer
from duplicate_detector import DuplicateDetector
from text_extractor import extract_text
from utils import (
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
    target_dir    : folder to scan and organise
    dry_run       : simulate without moving files
    recursive     : scan sub-folders too
    show_progress : show tqdm progress bar (CLI)
    """

    def __init__(
        self,
        target_dir: str,
        dry_run: bool = False,
        recursive: bool = False,
        show_progress: bool = False,
        smart_rename: bool = False,
        api_key: str = "",
    ):
        self.target_dir    = str(Path(target_dir).resolve())
        self.dry_run       = dry_run
        self.recursive     = recursive
        self.show_progress = show_progress

        self.classifier         = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.renamer            = SmartRenamer(api_key=api_key, enabled=smart_rename)

        self._stats: Dict = {
            "total_files":    0,
            "moved":          0,
            "duplicates":     0,
            "errors":         0,
            "low_confidence": 0,
            "by_category":    {cat: 0 for cat in self.classifier.categories},
        }

        # Map filename → extracted text (used by GUI for manual override)
        self._file_texts: Dict[str, str] = {}

        # Results list: (filename, category, confidence_pct, is_low, dest_path)
        self.results: List[Tuple[str, str, float, bool, str]] = []

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

        if self.show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(
                    files, desc="Organising", unit="file",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
                    colour="cyan",
                )
            except ImportError:
                iterator = files
        else:
            iterator = files

        for filepath in iterator:
            self._process_file(filepath)

        logger.info(sep)
        logger.info(
            "Run complete (%s). Moved: %d | Duplicates: %d | Low confidence: %d | Errors: %d",
            mode, self._stats["moved"], self._stats["duplicates"],
            self._stats["low_confidence"], self._stats["errors"],
        )
        logger.info(sep)
        return self._stats

    def apply_override(self, filename: str, correct_category: str) -> bool:
        """
        Apply a manual category override for a file.
        Teaches the classifier about the correction for future predictions.

        Returns True if override was applied successfully.
        """
        # Find the result entry for this file
        for i, (fname, old_cat, conf, is_low, dest) in enumerate(self.results):
            if fname == filename:
                # Move file from old category to new
                old_path = Path(dest)
                new_dir  = Path(self.target_dir) / correct_category

                if not old_path.exists():
                    logger.warning("Override: file not found at %s", old_path)
                    return False

                try:
                    new_dir.mkdir(parents=True, exist_ok=True)
                    new_path = new_dir / old_path.name
                    counter  = 1
                    while new_path.exists():
                        new_path = new_dir / f"{old_path.stem}_{counter}{old_path.suffix}"
                        counter += 1
                    old_path.rename(new_path)

                    # Update results record
                    self.results[i] = (fname, correct_category, conf, False, str(new_path))
                    logger.info(
                        "Override applied: '%s' → %s/ (was %s/)",
                        fname, correct_category, old_cat,
                    )

                    # Teach the classifier
                    text = self._file_texts.get(fname, "")
                    if text:
                        self.classifier.add_correction(text, correct_category)

                    return True
                except Exception as exc:
                    logger.error("Override failed for '%s': %s", filename, exc)
                    return False

        logger.warning("Override: file '%s' not found in results.", filename)
        return False

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

        # Store text for potential override
        self._file_texts[filename] = text

        # Classification with confidence
        try:
            category, confidence_pct, is_low = self.classifier.predict_with_confidence(text)
        except Exception as exc:
            logger.error("Classification error for '%s': %s", filename, exc)
            category, confidence_pct, is_low = "Other", 0.0, True

        # Log with confidence badge
        if is_low:
            logger.warning(
                "  ↳ Category: %s (%.1f%% — LOW CONFIDENCE ⚠️ review recommended)",
                category, confidence_pct,
            )
            self._stats["low_confidence"] += 1
        else:
            logger.info("  ↳ Category: %s (%.1f%% confident)", category, confidence_pct)

        # Smart rename
        new_filename = self.renamer.rename(filename, text)
        if new_filename != filename and not self.dry_run:
            try:
                new_filepath = str(Path(filepath).parent / new_filename)
                Path(filepath).rename(new_filepath)
                filepath = new_filepath
                filename = new_filename
            except Exception as exc:
                logger.warning("Rename failed: %s", exc)

        dest_dir  = str(Path(self.target_dir) / category)
        dest_path = str(Path(dest_dir) / filename)

        # Move or simulate
        if self.dry_run:
            logger.info("  [DRY RUN] '%s' → %s/", filename, category)
        else:
            try:
                dest_path = safe_move(filepath, dest_dir)
            except Exception as exc:
                logger.error("Move failed for '%s': %s", filename, exc)
                self._stats["errors"] += 1
                return

        self._stats["moved"] += 1
        self._stats["by_category"][category] = (
            self._stats["by_category"].get(category, 0) + 1
        )

        # Store result for potential override
        self.results.append((filename, category, confidence_pct, is_low, dest_path))
