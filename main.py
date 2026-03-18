"""
main.py
-------
Entry point for the Smart AI File Organizer.

Usage
-----
    python main.py "D:\\Downloads"                  # organise
    python main.py "D:\\Downloads" --dry-run        # preview
    python main.py "D:\\Downloads" --recursive      # include sub-folders
    python main.py "D:\\Downloads" --undo           # undo last run
    python main.py "D:\\Downloads" --undo --dry-run # preview undo
    python main.py "D:\\Downloads" -v               # verbose
    python gui.py                                   # launch GUI
"""

import argparse
import logging
import sys
from pathlib import Path

from organizer import FileOrganizer
from undo import undo_moves, print_undo_summary
from utils import print_summary, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smart_organizer",
        description=(
            "Smart AI File Organizer — classify and move files into category sub-folders.\n"
            "Supports PDF, DOCX, TXT, XLSX, PPTX, CSV, EML, MSG, ZIP, PNG, JPG."
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
        "--undo", action="store_true",
        help="Undo the last organise run — restore files to original locations.",
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

    # ── Undo mode ────────────────────────────────────────────────────────────
    if args.undo:
        mode = "DRY RUN" if args.dry_run else "LIVE"
        print(f"\n↩️  Smart AI File Organizer — Undo")
        print(f"   Target : {target}")
        print(f"   Mode   : {mode}\n")
        if args.dry_run:
            print("⚠️  DRY RUN — no files will be moved.\n")
        stats = undo_moves(str(target), dry_run=args.dry_run)
        print_undo_summary(stats, dry_run=args.dry_run)
        return 0

    # ── Organise mode ────────────────────────────────────────────────────────
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
        show_progress=True,     # show tqdm bar in CLI
    )
    stats = organizer.run()
    print_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
