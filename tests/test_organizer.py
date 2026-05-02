"""
tests/test_organizer.py
------------------------
Integration tests for FileOrganizer — uses dry_run=True so no files
are ever actually moved during testing.
"""

import pytest

from smart_ai_file_organizer.organizer import FileOrganizer


@pytest.fixture
def sample_folder(tmp_path):
    """Create a temp folder with a mix of sample files."""
    files = {
        "invoice.txt":  "invoice payment bank account balance tax revenue profit loss",
        "resume.txt":   "resume skills python java experience university degree GPA",
        "ai_notes.txt": "neural network deep learning transformer BERT model training",
        "diary.txt":    "dear diary birthday family vacation memories friend love",
        "manual.txt":   "user manual installation guide troubleshooting FAQ setup",
    }
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    return tmp_path


class TestFileOrganizerDryRun:
    def test_dry_run_returns_stats(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=True)
        stats = org.run()
        assert isinstance(stats, dict)
        assert "total_files" in stats
        assert "moved" in stats
        assert "duplicates" in stats
        assert "errors" in stats

    def test_dry_run_does_not_move_files(self, sample_folder):
        original_files = set(p.name for p in sample_folder.iterdir() if p.is_file())
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=True)
        org.run()
        remaining_files = set(p.name for p in sample_folder.iterdir() if p.is_file())
        assert original_files == remaining_files

    def test_dry_run_does_not_create_folders(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=True)
        org.run()
        # No sub-directories should be created in dry-run mode
        subdirs = [p for p in sample_folder.iterdir() if p.is_dir()]
        assert len(subdirs) == 0

    def test_correct_file_count(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=True)
        stats = org.run()
        assert stats["total_files"] == 5

    def test_no_errors_on_valid_files(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=True)
        stats = org.run()
        assert stats["errors"] == 0

    def test_duplicate_detection_in_dry_run(self, tmp_path):
        """Two files with identical content — one should be flagged as duplicate."""
        (tmp_path / "original.txt").write_text("invoice payment bank balance tax revenue")
        (tmp_path / "copy.txt").write_text("invoice payment bank balance tax revenue")

        org = FileOrganizer(target_dir=str(tmp_path), dry_run=True)
        stats = org.run()

        assert stats["duplicates"] == 1
        assert stats["total_files"] == 2


class TestFileOrganizerLive:
    def test_files_are_moved_to_category_folders(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=False)
        stats = org.run()

        # All files should have been moved (no errors, no duplicates)
        assert stats["moved"] == 5
        assert stats["errors"] == 0

        # Category sub-folders must exist
        categories = ["Finance", "Resume", "AI", "Research", "Personal", "Other"]
        created = [p.name for p in sample_folder.iterdir() if p.is_dir()]
        assert any(cat in created for cat in categories)

    def test_original_folder_has_no_txt_files_after_run(self, sample_folder):
        org = FileOrganizer(target_dir=str(sample_folder), dry_run=False)
        org.run()
        remaining_txt = list(sample_folder.glob("*.txt"))
        assert len(remaining_txt) == 0
