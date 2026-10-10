"""Command-line entry point for Smart AI File Organizer."""

from __future__ import annotations

import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .config import ConfigError, load_config
from .organizer import FileOrganizer
from .undo import print_undo_summary, undo_moves
from .utils import print_summary, setup_logging

PACKAGE_NAME = "smart-ai-file-organizer"


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.2.0"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for one-shot organization and undo operations."""
    parser = argparse.ArgumentParser(
        prog="smart-organizer",
        description=(
            "Smart AI File Organizer - classify and move files into category folders.\n"
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
        help="Preview what would happen - no files are moved.",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also scan and organize files inside subfolders.",
    )
    parser.add_argument(
        "--undo", action="store_true",
        help="Undo the latest organize run from structured history.",
    )
    parser.add_argument(
        "--smart-rename", action="store_true",
        help="Use AI to rename files based on their content (requires NVIDIA_API_KEY).",
    )
    parser.add_argument(
        "--config",
        help="Path to a custom config.json file.",
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
        "--yes", "-y", action="store_true",
        help="Skip the confirmation prompt for live runs (needed in scripts and cron jobs).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_package_version()}",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def confirm_live_run(target: Path, assume_yes: bool, smart_rename: bool) -> bool:
    """
    Ask before moving real files. Returns True when the run may proceed.

    With --yes the prompt is skipped. Without it, a non-interactive session
    (pipes, cron, CI) is refused instead of silently moving files.
    """
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print(
            "[ERROR] Live run needs confirmation, but this session is not interactive.\n"
            "        Re-run with --dry-run to preview, or --yes to proceed.",
            file=sys.stderr,
        )
        return False
    extra = " Text excerpts will be sent to the NVIDIA API for renaming." if smart_rename else ""
    answer = input(f"Move files in '{target}'? Undo stays available.{extra} [y/N]: ")
    return answer.strip().lower() in {"y", "yes"}


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
        print("\nSmart AI File Organizer - Undo")
        print(f"   Target : {target}")
        print(f"   Mode   : {mode}\n")
        if args.dry_run:
            print("DRY RUN - no files will be moved.\n")
        stats = undo_moves(
            str(target),
            dry_run=args.dry_run,
            history_path=args.history,
            run_id=args.run_id,
        )
        print_undo_summary(stats, dry_run=args.dry_run)
        return 0

    mode = "DRY RUN (preview)" if args.dry_run else "LIVE"
    history_display = args.history or target / ".smart-organizer" / "history.jsonl"
    print("\nSmart AI File Organizer")
    print(f"   Target    : {target}")
    print(f"   Mode      : {mode}")
    print(f"   Recursive : {args.recursive}")
    print(f"   Log       : {target / 'organizer.log'}")
    print(f"   History   : {history_display}\n")

    if args.dry_run:
        print("DRY RUN - no files will be moved.\n")
    else:
        print("LIVE MODE - files will be moved. Use --dry-run to preview first.\n")
        if not confirm_live_run(target, args.yes, args.smart_rename):
            print("Cancelled. No files were changed.")
            return 2

    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    api_key = cfg.get("smart_rename", {}).get("api_key", "")

    organizer = FileOrganizer(
        target_dir=str(target),
        dry_run=args.dry_run,
        recursive=args.recursive,
        show_progress=True,
        smart_rename=args.smart_rename,
        api_key=api_key,
        config_path=args.config,
        history_path=args.history,
    )
    stats = organizer.run()
    print_summary(stats, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
