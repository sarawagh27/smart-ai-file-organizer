"""
duplicate_detector.py
---------------------
Detects duplicate files using MD5 content hashing.

A duplicate is defined as two files with identical byte content,
regardless of their name or location.
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def compute_md5(filepath: str, chunk_size: int = 8192) -> Optional[str]:
    """
    Compute the MD5 hash of a file's contents.

    Parameters
    ----------
    filepath  : path to the file
    chunk_size: bytes read per iteration (keeps memory use low for large files)

    Returns
    -------
    Hex-encoded MD5 string, or None on I/O error.
    """
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as e:
        logger.error("Could not hash %s: %s", filepath, e)
        return None


class DuplicateDetector:
    """
    Tracks file hashes and identifies duplicates.

    Usage
    -----
    detector = DuplicateDetector()
    is_dup, original = detector.check(filepath)
    if is_dup:
        print(f"{filepath} is a duplicate of {original}")
    """

    def __init__(self):
        # Maps MD5 hash → first file path seen with that hash
        self._seen: Dict[str, str] = {}

    def check(self, filepath: str) -> tuple[bool, Optional[str]]:
        """
        Check whether a file is a duplicate of one already seen.

        Returns
        -------
        (is_duplicate, original_path)
            is_duplicate  : True if a file with the same content was seen before
            original_path : path of the first file with this hash (None if new)
        """
        md5 = compute_md5(filepath)
        if md5 is None:
            # Cannot determine — treat as non-duplicate to be safe
            return False, None

        if md5 in self._seen:
            original = self._seen[md5]
            logger.info(
                "Duplicate detected: '%s' matches '%s' (MD5: %s)",
                filepath, original, md5,
            )
            return True, original

        # First time we see this hash — register it
        self._seen[md5] = filepath
        return False, None

    def reset(self) -> None:
        """Clear the internal hash registry."""
        self._seen.clear()

    def summary(self) -> Dict[str, List[str]]:
        """
        Return a dict mapping each hash to all files sharing that hash.
        Only hashes with more than one file are included.
        (Useful after bulk processing to get a full duplicate report.)
        """
        # Build reverse mapping: hash → [list of all paths]
        reverse: Dict[str, List[str]] = {}
        for md5, path in self._seen.items():
            reverse.setdefault(md5, []).append(path)
        return {h: paths for h, paths in reverse.items() if len(paths) > 1}
