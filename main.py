"""
main.py
-------
Entry point for the Smart AI File Organizer.

Usage
-----
    python main.py                                  # current directory
    python main.py "D:\\Downloads"                  # specific folder
    python main.py "D:\\Downloads" --dry-run        # preview only
    python main.py "D:\\Downloads" --recursive      # include sub-folders
    python main.py "D:\\Downloads" -v               # verbose logging
    python gui.py                                   # launch the GUI
"""

import argparse
import logging
import sys
from pathlib import Path

from organizer import FileOrganizer
from utils import print_summary, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smart_organizer",
        description=(
            "Smart AI File Organizer — classify and move PDF, DOCX, TXT,\n"
            "XLSX, PPTX, CSV, and image files into category sub-folders."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="Folder to organise (default: current directory).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would happen — no files are moved.",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also scan and organise files inside sub-folders.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"[ERROR] Directory not found: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"[ERROR] Not a directory: {target}", file=sys.stderr)
        return 1

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_dir=str(target), level=log_level)

    mode = "DRY RUN (preview)" if args.dry_run else "LIVE"
    print(f"\n🗂  Smart AI File Organizer")
    print(f"   Target    : {target}")
    print(f"   Mode      : {mode}")
    print(f"   Recursive : {args.recursive}")
    print(f"   Log       : {target / 'organizer.log'}\n")

    if args.dry_run:
        print("⚠️  DRY RUN — no files will be moved.\n")

    organizer = FileOrganizer(
        target_dir=str(target),
        dry_run=args.dry_run,
        recursive=args.recursive,
    )
    stats = organizer.run()
    print_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
