"""
tests/test_text_extractor.py
-----------------------------
Unit tests for text extraction functions.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from text_extractor import extract_text, extract_from_txt


class TestExtractFromTxt:
    def test_reads_plain_text(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("Hello from a text file.")
        result = extract_from_txt(str(f))
        assert "Hello from a text file." in result

    def test_returns_empty_string_for_missing_file(self):
        result = extract_from_txt("/nonexistent/file.txt")
        assert result == ""

    def test_handles_utf8_content(self, tmp_path):
        f = tmp_path / "unicode.txt"
        f.write_text("Héllo Wörld — unicode content", encoding="utf-8")
        result = extract_from_txt(str(f))
        assert len(result) > 0


class TestExtractText:
    def test_dispatches_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("dispatch test content")
        result = extract_text(str(f))
        assert "dispatch test content" in result

    def test_unsupported_extension_returns_empty(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("unsupported")
        result = extract_text(str(f))
        assert result == ""

    def test_returns_string_type(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("type check")
        result = extract_text(str(f))
        assert isinstance(result, str)

    def test_empty_file_returns_empty_string(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = extract_text(str(f))
        assert result == ""
