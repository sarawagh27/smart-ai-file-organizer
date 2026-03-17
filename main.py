"""
main.py
-------
Entry point for the Smart AI File Organizer.

Usage
-----
    python main.py                        # organises the current directory
    python main.py /path/to/folder        # organises the given folder
    python main.py /path/to/folder -v     # verbose (DEBUG) logging
    python main.py --help                 # show help
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
            "Smart AI File Organizer — automatically classifies and moves\n"
            "PDF, TXT, and DOCX files into category sub-folders using ML."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to the folder you want to organise (default: current directory).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Resolve and validate target directory
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"[ERROR] Directory not found: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"[ERROR] Not a directory: {target}", file=sys.stderr)
        return 1

    # Set up logging (log file lives inside the target directory)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_dir=str(target), level=log_level)

    print(f"\n🗂  Smart AI File Organizer")
    print(f"   Target : {target}")
    print(f"   Log    : {target / 'organizer.log'}\n")

    # Run the organizer
    organizer = FileOrganizer(target_dir=str(target))
    stats = organizer.run()

    # Print summary table
    print_summary(stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
