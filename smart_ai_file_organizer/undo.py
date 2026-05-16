"""
Undo the latest Smart AI File Organizer run from structured operation history.

The current undo path reads ``.smart-organizer/history.jsonl`` instead of
scraping human-readable log lines. A legacy ``organizer.log`` parser remains as
a fallback for folders organized by older releases.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from .duplicate_detector import compute_md5
from .history import OperationHistory
from .utils import setup_logging

logger = logging.getLogger(__name__)

MOVE_PATTERN = re.compile(r"Moved '(.+?)' .+? '(.+?)'")


def parse_moves_from_log(log_path: str) -> list[tuple[str, str]]:
    """Parse legacy organizer.log move lines, newest first."""
    moves: list[tuple[str, str]] = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = MOVE_PATTERN.search(line)
                if match:
                    filename = match.group(1)
                    dest = match.group(2)
                    moves.append((filename, dest))
    except FileNotFoundError:
        logger.error("Log file not found: %s", log_path)
    except Exception as e:
        logger.error("Error reading log: %s", e)
    return list(reversed(moves))


def undo_moves(
    target_dir: str,
    dry_run: bool = False,
    history_path: str | Path | None = None,
    run_id: str | None = None,
) -> dict:
    """
    Reverse one run from structured history.

    Returns stats dict with keys: found, restored, skipped, errors.
    """
    target = Path(target_dir).resolve()
    stats = {"found": 0, "restored": 0, "skipped": 0, "errors": 0}

    history = OperationHistory.for_target(target, history_path)
    records = history.records_for_undo(run_id=run_id)
    stats["found"] = len(records)

    if not records:
        legacy_stats = _undo_legacy_log(target, dry_run=dry_run)
        if legacy_stats["found"]:
            return legacy_stats
        logger.error("No operation history found in '%s'. Nothing to undo.", history.path)
        return stats

    logger.info("Found %d operation(s) to undo.", len(records))

    for record in records:
        source = Path(record.source_path)
        dest = Path(record.destination_path)

        if not dest.exists():
            logger.warning("File no longer at destination - skipping: %s", dest)
            stats["skipped"] += 1
            continue

        current_hash = compute_md5(str(dest))
        if record.destination_hash and current_hash and current_hash != record.destination_hash:
            logger.warning("File changed since organize run - skipping: %s", dest)
            stats["skipped"] += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would restore: '%s' -> '%s'", dest, source)
            stats["restored"] += 1
            continue

        try:
            source.parent.mkdir(parents=True, exist_ok=True)
            restore_path = source
            counter = 1
            while restore_path.exists():
                restore_path = source.with_name(
                    f"{source.stem}_restored_{counter}{source.suffix}"
                )
                counter += 1

            dest.rename(restore_path)
            logger.info("Restored: '%s' -> '%s'", dest, restore_path)
            stats["restored"] += 1
        except Exception as e:
            logger.error("Failed to restore '%s': %s", dest, e)
            stats["errors"] += 1

    return stats


def _undo_legacy_log(target: Path, dry_run: bool = False) -> dict:
    """Fallback for folders organized before structured history existed."""
    stats = {"found": 0, "restored": 0, "skipped": 0, "errors": 0}
    moves = parse_moves_from_log(str(target / "organizer.log"))
    stats["found"] = len(moves)
    if not moves:
        return stats

    logger.warning("Using legacy organizer.log undo fallback.")
    for _, dest_path in moves:
        dest = Path(dest_path)
        original = target / dest.name
        if not dest.exists():
            stats["skipped"] += 1
            continue
        if dry_run:
            logger.info("[DRY RUN] Would restore: '%s' -> '%s'", dest, original)
            stats["restored"] += 1
            continue
        try:
            restore_path = original
            counter = 1
            while restore_path.exists():
                restore_path = target / f"{dest.stem}_restored_{counter}{dest.suffix}"
                counter += 1
            dest.rename(restore_path)
            stats["restored"] += 1
        except Exception as e:
            logger.error("Failed to restore legacy move '%s': %s", dest, e)
            stats["errors"] += 1
    return stats


def print_undo_summary(stats: dict, dry_run: bool = False) -> None:
    width = 46
    print(f"\n{'=' * width}")
    print(f"  {'Smart AI File Organizer - Undo':^{width - 4}}")
    if dry_run:
        print("  *** DRY RUN - no files were moved ***")
    print(f"{'=' * width}")
    print(f"  Operations found   : {stats.get('found', 0)}")
    label = "Would restore" if dry_run else "Restored"
    print(f"  {label:<20}: {stats.get('restored', 0)}")
    print(f"  Skipped            : {stats.get('skipped', 0)}")
    print(f"  Errors             : {stats.get('errors', 0)}")
    print(f"{'=' * width}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="undo",
        description="Undo the latest Smart AI File Organizer run.",
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="The folder that was organized (default: current directory).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be restored without moving anything.",
    )
    parser.add_argument(
        "--history",
        help="Path to the structured operation history file.",
    )
    parser.add_argument(
        "--run-id",
        help="Undo a specific run id instead of the latest run.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    target = Path(args.directory).resolve()
    if not target.exists() or not target.is_dir():
        print(f"[ERROR] Invalid directory: {target}", file=sys.stderr)
        return 1

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_dir=str(target), level=log_level)

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print("\nSmart AI File Organizer - Undo")
    print(f"   Target : {target}")
    print(f"   Mode   : {mode}\n")

    stats = undo_moves(
        str(target),
        dry_run=args.dry_run,
        history_path=args.history,
        run_id=args.run_id,
    )
    print_undo_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
