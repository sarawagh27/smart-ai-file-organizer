"""
Command-line entry point for Smart AI File Organizer.

Usage
-----
    smart-organizer "D:\\Downloads"                 # organize
    smart-organizer "D:\\Downloads" --dry-run       # preview
    smart-organizer "D:\\Downloads" --recursive     # include subfolders
    smart-organizer "D:\\Downloads" --undo          # undo last run
    smart-organizer-gui                             # launch GUI
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .organizer import FileOrganizer
from .undo import print_undo_summary, undo_moves
from .utils import print_summary, setup_logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for one-shot organization and undo operations."""
    parser = argparse.ArgumentParser(
        prog="smart-organizer",
        description=(
            "Smart AI File Organizer — classify and move files into category folders.\n"
            "Supports PDF, DOCX, TXT, XLSX, PPTX, CSV, EML, MSG, ZIP, PNG, JPG."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="Folder to organize (default: current directory).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would happen — no files are moved.",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also scan and organize files inside subfolders.",
    )
    parser.add_argument(
        "--undo", action="store_true",
        help="Undo the last organize run — restore files to original locations.",
    )
    parser.add_argument(
        "--smart-rename", action="store_true",
        help="Use AI to rename files based on their content (requires NVIDIA_API_KEY).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CLI and return a process exit code."""
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

    if args.undo:
        mode = "DRY RUN" if args.dry_run else "LIVE"
        print("\nSmart AI File Organizer — Undo")
        print(f"   Target : {target}")
        print(f"   Mode   : {mode}\n")
        if args.dry_run:
            print("DRY RUN — no files will be moved.\n")
        stats = undo_moves(str(target), dry_run=args.dry_run)
        print_undo_summary(stats, dry_run=args.dry_run)
        return 0

    mode = "DRY RUN (preview)" if args.dry_run else "LIVE"
    print("\nSmart AI File Organizer")
    print(f"   Target    : {target}")
    print(f"   Mode      : {mode}")
    print(f"   Recursive : {args.recursive}")
    print(f"   Log       : {target / 'organizer.log'}\n")

    if args.dry_run:
        print("DRY RUN — no files will be moved.\n")

    cfg_path = PROJECT_ROOT / "config.json"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON in {cfg_path}: {exc}", file=sys.stderr)
        return 1
    api_key = cfg.get("smart_rename", {}).get("api_key", "")

    organizer = FileOrganizer(
        target_dir=str(target),
        dry_run=args.dry_run,
        recursive=args.recursive,
        show_progress=True,
        smart_rename=args.smart_rename,
        api_key=api_key,
    )
    stats = organizer.run()
    print_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
