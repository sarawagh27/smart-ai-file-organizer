"""Compatibility wrapper for the Smart AI File Organizer CLI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smart_ai_file_organizer.main import main


if __name__ == "__main__":
    raise SystemExit(main())
