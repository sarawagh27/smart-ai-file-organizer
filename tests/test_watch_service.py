from smart_ai_file_organizer.duplicate_detector import DuplicateDetector
from smart_ai_file_organizer.history import OperationHistory
from smart_ai_file_organizer.watch_service import process_watch_file, should_process_path


class FakeClassifier:
    categories = ["Finance", "Other"]

    def predict(self, text):
        return "Finance" if "invoice" in text else "Other"


def test_should_process_path_accepts_supported_top_level_file(tmp_path):
    file_path = tmp_path / "invoice.txt"
    file_path.write_text("invoice")

    assert should_process_path(file_path, tmp_path)


def test_should_process_path_rejects_nested_or_unsupported_files(tmp_path):
    nested = tmp_path / "Finance"
    nested.mkdir()
    nested_file = nested / "invoice.txt"
    nested_file.write_text("invoice")
    unsupported = tmp_path / "image.bmp"
    unsupported.write_text("bits")

    assert not should_process_path(nested_file, tmp_path)
    assert not should_process_path(unsupported, tmp_path)


def test_process_watch_file_moves_and_records_history(tmp_path):
    file_path = tmp_path / "invoice.txt"
    file_path.write_text("invoice payment bank")
    history = OperationHistory.for_target(tmp_path)

    result = process_watch_file(
        filepath=file_path,
        target_dir=tmp_path,
        classifier=FakeClassifier(),
        duplicate_detector=DuplicateDetector(),
        history=history,
    )

    assert result.status == "moved"
    assert result.category == "Finance"
    assert (tmp_path / "Finance" / "invoice.txt").exists()
    records = history.read_records()
    assert len(records) == 1
    assert records[0].action == "move"


def test_process_watch_file_reports_duplicate(tmp_path):
    detector = DuplicateDetector()
    original = tmp_path / "a.txt"
    duplicate = tmp_path / "b.txt"
    original.write_text("same")
    duplicate.write_text("same")
    detector.check(str(original))

    result = process_watch_file(
        filepath=duplicate,
        target_dir=tmp_path,
        classifier=FakeClassifier(),
        duplicate_detector=detector,
        history=OperationHistory.for_target(tmp_path),
    )

    assert result.status == "duplicate"
    assert duplicate.exists()
