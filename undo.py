"""
undo.py
-------
Undo the last organise run by reading organizer.log and reversing
every file move recorded in it.

How it works
------------
  1. Parse organizer.log for lines containing "Moved 'X' → 'Y'"
  2. For each move, move the file back from Y to its original location
  3. Log all undo operations

Usage
-----
    python undo.py                        # undo in current directory
    python undo.py "D:\\Downloads"        # undo in specific folder
    python undo.py "D:\\Downloads" --dry-run  # preview what would be undone
"""

import argparse
import logging
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import setup_logging

logger = logging.getLogger(__name__)

# Regex to match log lines like:
# 2026-03-18 10:22:01 | INFO     | utils | Moved 'filename.pdf' → '/path/to/Category/filename.pdf'
MOVE_PATTERN = re.compile(
    r"Moved '(.+?)' → '(.+?)'"
)


def parse_moves_from_log(log_path: str) -> list[tuple[str, str]]:
    """
    Parse organizer.log and return a list of (original_name, destination_path) tuples.
    Returns moves in reverse order (most recent first) so undo is LIFO.
    """
    moves = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = MOVE_PATTERN.search(line)
                if match:
                    filename = match.group(1)   # original filename
                    dest     = match.group(2)   # full destination path
                    moves.append((filename, dest))
    except FileNotFoundError:
        logger.error("Log file not found: %s", log_path)
    except Exception as e:
        logger.error("Error reading log: %s", e)

    # Reverse so most recent moves are undone first
    return list(reversed(moves))


def undo_moves(
    target_dir: str,
    dry_run: bool = False,
) -> dict:
    """
    Read organizer.log from target_dir and reverse all file moves.

    Returns stats dict with keys: found, restored, skipped, errors
    """
    target   = Path(target_dir).resolve()
    log_path = target / "organizer.log"

    stats = {"found": 0, "restored": 0, "skipped": 0, "errors": 0}

    if not log_path.exists():
        logger.error("No organizer.log found in '%s'. Nothing to undo.", target)
        return stats

    moves = parse_moves_from_log(str(log_path))
    stats["found"] = len(moves)

    if not moves:
        logger.warning("No file moves found in the log. Nothing to undo.")
        return stats

    logger.info("Found %d move(s) to undo.", len(moves))

    for filename, dest_path in moves:
        dest = Path(dest_path)

        # The original location is the target_dir (top level)
        original = target / dest.name

        if not dest.exists():
            logger.warning("File no longer at destination — skipping: %s", dest.name)
            stats["skipped"] += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would restore: '%s' → '%s'", dest.name, target)
            stats["restored"] += 1
            continue

        try:
            # Handle name collision at original location
            restore_path = original
            counter = 1
            while restore_path.exists():
                restore_path = target / f"{dest.stem}_restored_{counter}{dest.suffix}"
                counter += 1

            dest.rename(restore_path)
            logger.info("Restored: '%s' → '%s'", dest.name, restore_path.parent)
            stats["restored"] += 1

        except Exception as e:
            logger.error("Failed to restore '%s': %s", dest.name, e)
            stats["errors"] += 1

    return stats


def print_undo_summary(stats: dict, dry_run: bool = False) -> None:
    width = 46
    print(f"\n{'━' * width}")
    print(f"  {'Smart AI File Organizer — Undo':^{width - 4}}")
    if dry_run:
        print(f"\033[93m  *** DRY RUN — no files were moved ***\033[0m")
    print(f"{'━' * width}")
    print(f"  Moves found in log : {stats.get('found', 0)}")
    label = "Would restore" if dry_run else "Restored"
    print(f"  {label:<20}: {stats.get('restored', 0)}")
    print(f"  Skipped (missing)  : {stats.get('skipped', 0)}")
    print(f"  Errors             : {stats.get('errors', 0)}")
    print(f"{'━' * width}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="undo",
        description="Undo the last Smart AI File Organizer run — restore files to original locations.",
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="The folder that was organised (default: current directory).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be restored without moving anything.",
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
    print(f"\n↩️  Smart AI File Organizer — Undo")
    print(f"   Target : {target}")
    print(f"   Mode   : {mode}\n")

    stats = undo_moves(str(target), dry_run=args.dry_run)
    print_undo_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
