"""Testable watch-mode file processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .classifier import DocumentClassifier
from .duplicate_detector import DuplicateDetector, compute_md5
from .history import OperationHistory, new_run_id
from .text_extractor import SUPPORTED_EXTENSIONS, extract_text
from .utils import safe_move

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WatchProcessResult:
    status: str
    source_path: str
    category: str | None = None
    destination_path: str | None = None
    reason: str | None = None


def should_process_path(filepath: str | Path, target_dir: str | Path) -> bool:
    """Return True when a watch event points to a supported top-level file."""
    path = Path(filepath).resolve()
    target = Path(target_dir).resolve()
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False
    try:
        relative = path.relative_to(target)
    except ValueError:
        return False
    return len(relative.parts) == 1


def process_watch_file(
    filepath: str | Path,
    target_dir: str | Path,
    classifier: DocumentClassifier,
    duplicate_detector: DuplicateDetector,
    history: OperationHistory,
) -> WatchProcessResult:
    """Extract, classify, move, and record one file detected by watch mode."""
    source = Path(filepath).resolve()
    if not source.exists():
        return WatchProcessResult("skipped", str(source), reason="missing")

    is_dup, original = duplicate_detector.check(str(source))
    if is_dup:
        reason = f"duplicate of {Path(original).name}" if original else "duplicate"
        logger.warning("DUPLICATE - skipping '%s' (%s)", source.name, reason)
        return WatchProcessResult("duplicate", str(source), reason=reason)

    text = extract_text(str(source))
    if not text.strip():
        logger.warning("No text extracted from '%s'; classifying as 'Other'.", source.name)

    try:
        category = classifier.predict(text)
    except RuntimeError:
        raise
    except Exception as exc:
        logger.error("Classification error for '%s': %s", source.name, exc)
        category = "Other"

    file_hash = compute_md5(str(source))
    dest_path = safe_move(str(source), str(Path(target_dir).resolve() / category))
    history.record(
        run_id=new_run_id(),
        action="move",
        source_path=source,
        destination_path=dest_path,
        source_hash=file_hash,
        destination_hash=file_hash,
    )
    logger.info("Moved watched file '%s' to %s/", source.name, category)
    return WatchProcessResult(
        "moved",
        str(source),
        category=category,
        destination_path=dest_path,
    )
