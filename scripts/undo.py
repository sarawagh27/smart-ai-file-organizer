"""Compatibility wrapper for undo mode."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smart_ai_file_organizer.undo import main


if __name__ == "__main__":
    raise SystemExit(main())
