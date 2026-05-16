"""Watch Mode for Smart AI File Organizer."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .classifier import DocumentClassifier
from .duplicate_detector import DuplicateDetector
from .history import OperationHistory
from .utils import create_category_folders, setup_logging
from .watch_service import process_watch_file, should_process_path

logger = logging.getLogger(__name__)


class FileOrganizerHandler(FileSystemEventHandler):
    """Watchdog event handler for new supported top-level files."""

    def __init__(
        self,
        target_dir: str,
        classifier: DocumentClassifier,
        duplicate_detector: DuplicateDetector,
        delay: float = 2.0,
        recursive: bool = False,
        history_path: str | Path | None = None,
    ):
        super().__init__()
        self.target_dir = Path(target_dir).resolve()
        self.classifier = classifier
        self.duplicate_detector = duplicate_detector
        self.delay = delay
        self.recursive = recursive
        self.history = OperationHistory.for_target(self.target_dir, history_path)
        self._processing: set[str] = set()

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)

    def _handle(self, filepath: str):
        path = Path(filepath).resolve()
        if not should_process_path(path, self.target_dir):
            return
        if str(path) in self._processing:
            return

        self._processing.add(str(path))
        try:
            logger.info("New file detected: %s - waiting %.1fs...", path.name, self.delay)
            time.sleep(self.delay)
            if not path.exists():
                logger.warning("File no longer exists: %s", path.name)
                return
            self._process(str(path))
        finally:
            self._processing.discard(str(path))

    def _process(self, filepath: str):
        try:
            result = process_watch_file(
                filepath=filepath,
                target_dir=self.target_dir,
                classifier=self.classifier,
                duplicate_detector=self.duplicate_detector,
                history=self.history,
            )
            if result.status == "moved":
                logger.info("Moved to %s/", result.category)
        except Exception as exc:
            logger.error("Watch processing failed for '%s': %s", Path(filepath).name, exc)


class FolderWatcher:
    """Manages the watchdog Observer lifecycle."""

    def __init__(
        self,
        target_dir: str,
        delay: float = 2.0,
        recursive: bool = False,
        history_path: str | Path | None = None,
    ):
        self.target_dir = str(Path(target_dir).resolve())
        self.delay = delay
        self.recursive = recursive

        logger.info("Training document classifier...")
        self.classifier = DocumentClassifier()
        self.classifier.train()
        logger.info("Classifier ready - %d categories.", len(self.classifier.categories))

        create_category_folders(self.target_dir, self.classifier.categories)

        self.duplicate_detector = DuplicateDetector()
        self.handler = FileOrganizerHandler(
            target_dir=self.target_dir,
            classifier=self.classifier,
            duplicate_detector=self.duplicate_detector,
            delay=self.delay,
            recursive=self.recursive,
            history_path=history_path,
        )
        self.observer = Observer()

    def start(self):
        """Start watching and block until interrupted."""
        self.observer.schedule(
            self.handler,
            path=self.target_dir,
            recursive=self.recursive,
        )
        self.observer.start()

        logger.info("=" * 60)
        logger.info("WATCH MODE ACTIVE")
        logger.info("    Folder    : %s", self.target_dir)
        logger.info("    Recursive : %s", self.recursive)
        logger.info("    Delay     : %.1fs", self.delay)
        logger.info("    Press Ctrl+C to stop.")
        logger.info("=" * 60)

        print(f"\nWatching: {self.target_dir}")
        print("   Drop any supported file into the folder and it will be organized automatically.")
        print("   Press Ctrl+C to stop.\n")

        try:
            while self.observer.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Watch mode stopped by user.")
            print("\n\nWatch mode stopped.")
        finally:
            self.observer.stop()
            self.observer.join()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="watcher",
        description=(
            "Smart AI File Organizer - Watch Mode\n"
            "Monitors a folder and automatically organizes new files as they arrive."
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
        "--history",
        help="Path to the structured operation history file.",
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
        target_dir=str(target),
        delay=args.delay,
        recursive=args.recursive,
        history_path=args.history,
    )
    watcher.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
