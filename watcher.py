"""
watcher.py
----------
Watch Mode for the Smart AI File Organizer.

Monitors a folder in real-time using the watchdog library.
Whenever a new supported file is created or moved into the folder,
it is automatically extracted, classified, and moved into the
correct category sub-folder.

Usage
-----
    python watcher.py "D:\\Downloads"
    python watcher.py "D:\\Downloads" --recursive
    python watcher.py "D:\\Downloads" --delay 3
    python watcher.py --help

How it works
------------
    1. Start watching the target folder
    2. When a new file appears (created or moved in):
       - Wait a short delay (file may still be writing)
       - Check if it's a supported file type
       - Extract text, classify, move to category folder
    3. Log all activity to organizer.log
    4. Press Ctrl+C to stop watching
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from classifier import DocumentClassifier
from duplicate_detector import DuplicateDetector
from text_extractor import extract_text, SUPPORTED_EXTENSIONS
from utils import create_category_folders, safe_move, setup_logging


logger = logging.getLogger(__name__)


class FileOrganizerHandler(FileSystemEventHandler):
    """
    Watchdog event handler.
    Triggered whenever a file is created or moved into the watched folder.
    """

    def __init__(
        self,
        target_dir: str,
        classifier: DocumentClassifier,
        duplicate_detector: DuplicateDetector,
        delay: float = 2.0,
        recursive: bool = False,
    ):
        super().__init__()
        self.target_dir        = Path(target_dir).resolve()
        self.classifier        = classifier
        self.duplicate_detector = duplicate_detector
        self.delay             = delay      # seconds to wait before processing
        self.recursive         = recursive
        self._processing       = set()     # track files currently being processed

    def on_created(self, event):
        """Called when a file is created in the watched folder."""
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        """Called when a file is moved INTO the watched folder."""
        if not event.is_directory:
            self._handle(event.dest_path)

    def _handle(self, filepath: str):
        """Process a single new file."""
        path = Path(filepath).resolve()

        # Skip unsupported file types
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Skip files already inside a category sub-folder
        try:
            relative = path.relative_to(self.target_dir)
            if len(relative.parts) > 1:
                return
        except ValueError:
            return

        # Skip if already processing this file
        if str(path) in self._processing:
            return

        self._processing.add(str(path))

        # Wait for the file to finish writing before processing
        logger.info("🔍 New file detected: %s — waiting %.1fs...", path.name, self.delay)
        time.sleep(self.delay)

        # Make sure file still exists (wasn't immediately deleted)
        if not path.exists():
            logger.warning("File no longer exists: %s", path.name)
            self._processing.discard(str(path))
            return

        self._process(str(path))
        self._processing.discard(str(path))

    def _process(self, filepath: str):
        """Extract → classify → move."""
        filename = Path(filepath).name

        # Duplicate check
        is_dup, original = self.duplicate_detector.check(filepath)
        if is_dup:
            logger.warning(
                "DUPLICATE — skipping '%s' (matches '%s')",
                filename, Path(original).name,
            )
            return

        # Text extraction
        try:
            text = extract_text(filepath)
        except Exception as exc:
            logger.error("Extraction error for '%s': %s", filename, exc)
            return

        if not text.strip():
            logger.warning("No text extracted from '%s'; classifying as 'Other'.", filename)

        # Classification
        try:
            category = self.classifier.predict(text)
        except Exception as exc:
            logger.error("Classification error for '%s': %s", filename, exc)
            category = "Other"

        logger.info("  ↳ '%s' classified as: %s", filename, category)

        # Move to category folder
        dest_dir = str(self.target_dir / category)
        try:
            safe_move(filepath, dest_dir)
            logger.info("  ✅ Moved to %s/", category)
        except Exception as exc:
            logger.error("Move failed for '%s': %s", filename, exc)


class FolderWatcher:
    """
    Manages the watchdog Observer lifecycle.

    Usage
    -----
    watcher = FolderWatcher("D:\\Downloads", delay=2.0)
    watcher.start()   # blocks until Ctrl+C
    """

    def __init__(self, target_dir: str, delay: float = 2.0, recursive: bool = False):
        self.target_dir = str(Path(target_dir).resolve())
        self.delay      = delay
        self.recursive  = recursive

        # Train classifier once at startup
        logger.info("Training document classifier…")
        self.classifier = DocumentClassifier()
        self.classifier.train()
        logger.info(
            "Classifier ready — %d categories.",
            len(self.classifier.categories),
        )

        # Create category folders upfront
        create_category_folders(self.target_dir, self.classifier.categories)

        self.duplicate_detector = DuplicateDetector()
        self.handler = FileOrganizerHandler(
            target_dir        = self.target_dir,
            classifier        = self.classifier,
            duplicate_detector = self.duplicate_detector,
            delay             = self.delay,
            recursive         = self.recursive,
        )
        self.observer = Observer()

    def start(self):
        """Start watching — blocks until KeyboardInterrupt."""
        self.observer.schedule(
            self.handler,
            path      = self.target_dir,
            recursive = self.recursive,
        )
        self.observer.start()

        logger.info("=" * 60)
        logger.info("👁  WATCH MODE ACTIVE")
        logger.info("    Folder    : %s", self.target_dir)
        logger.info("    Recursive : %s", self.recursive)
        logger.info("    Delay     : %.1fs", self.delay)
        logger.info("    Press Ctrl+C to stop.")
        logger.info("=" * 60)

        print(f"\n👁  Watching: {self.target_dir}")
        print(f"   Drop any supported file into the folder and it will be organised automatically.")
        print(f"   Press Ctrl+C to stop.\n")

        try:
            while self.observer.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Watch mode stopped by user.")
            print("\n\n⛔  Watch mode stopped.")
        finally:
            self.observer.stop()
            self.observer.join()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="watcher",
        description=(
            "Smart AI File Organizer — Watch Mode\n"
            "Monitors a folder and automatically organises new files as they arrive."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="Folder to watch (default: current directory).",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds to wait after a file appears before processing (default: 2.0).",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also watch sub-folders.",
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

    watcher = FolderWatcher(
        target_dir = str(target),
        delay      = args.delay,
        recursive  = args.recursive,
    )
    watcher.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
