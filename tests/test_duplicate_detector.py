"""
tests/test_duplicate_detector.py
---------------------------------
Unit tests for the DuplicateDetector.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from duplicate_detector import DuplicateDetector, compute_md5


class TestComputeMd5:
    def test_returns_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = compute_md5(str(f))
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hex digest is always 32 chars

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("identical content")
        f2.write_text("identical content")
        assert compute_md5(str(f1)) == compute_md5(str(f2))

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content one")
        f2.write_text("content two")
        assert compute_md5(str(f1)) != compute_md5(str(f2))

    def test_returns_none_for_missing_file(self):
        result = compute_md5("/nonexistent/path/file.txt")
        assert result is None


class TestDuplicateDetector:
    @pytest.fixture
    def detector(self):
        return DuplicateDetector()

    def test_first_file_is_not_duplicate(self, detector, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("some unique content abc123")
        is_dup, original = detector.check(str(f))
        assert is_dup is False
        assert original is None

    def test_identical_file_is_duplicate(self, detector, tmp_path):
        f1 = tmp_path / "original.txt"
        f2 = tmp_path / "copy.txt"
        f1.write_text("duplicate content here")
        f2.write_text("duplicate content here")

        detector.check(str(f1))
        is_dup, original = detector.check(str(f2))

        assert is_dup is True
        assert original == str(f1)

    def test_different_files_not_duplicate(self, detector, tmp_path):
        f1 = tmp_path / "file1.txt"
        f2 = tmp_path / "file2.txt"
        f1.write_text("content alpha")
        f2.write_text("content beta")

        detector.check(str(f1))
        is_dup, _ = detector.check(str(f2))

        assert is_dup is False

    def test_reset_clears_registry(self, detector, tmp_path):
        f1 = tmp_path / "file.txt"
        f2 = tmp_path / "copy.txt"
        f1.write_text("reset test content")
        f2.write_text("reset test content")

        detector.check(str(f1))
        detector.reset()

        # After reset, the "copy" should no longer be seen as a duplicate
        is_dup, _ = detector.check(str(f2))
        assert is_dup is False

    def test_multiple_files_tracked(self, detector, tmp_path):
        files = []
        for i in range(5):
            f = tmp_path / f"file_{i}.txt"
            f.write_text(f"unique content number {i}")
            files.append(f)

        for f in files:
            is_dup, _ = detector.check(str(f))
            assert is_dup is False

    def test_summary_reports_duplicate_groups(self, detector, tmp_path):
        f1 = tmp_path / "original.txt"
        f2 = tmp_path / "copy.txt"
        f1.write_text("shared content")
        f2.write_text("shared content")

        detector.check(str(f1))
        detector.check(str(f2))

        summary = detector.summary()
        groups = list(summary.values())
        assert len(groups) == 1
        assert groups[0] == [str(f1), str(f2)]
