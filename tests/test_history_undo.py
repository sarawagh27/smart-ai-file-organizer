import json

from smart_ai_file_organizer.history import OperationHistory
from smart_ai_file_organizer.organizer import FileOrganizer
from smart_ai_file_organizer.renamer import SmartRenamer
from smart_ai_file_organizer.undo import undo_moves


def _write_config(tmp_path):
    config = {
        "categories": ["Finance", "Other"],
        "training_data": {
            "Finance": ["invoice payment bank account tax revenue"],
            "Other": ["manual guide general notes"],
        },
        "classifier": {
            "confidence_threshold": 0.18,
            "ngram_range": [1, 2],
            "naive_bayes_alpha": 0.4,
        },
        "organizer": {
            "supported_extensions": [".txt"],
            "fallback_category": "Other",
        },
        "smart_rename": {"enabled": False, "api_key": ""},
        "corrections": [],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_live_run_writes_history_and_undo_restores_file(tmp_path):
    config_path = _write_config(tmp_path)
    (tmp_path / "invoice.txt").write_text("invoice payment bank account tax revenue")

    organizer = FileOrganizer(str(tmp_path), config_path=config_path)
    stats = organizer.run()

    history_path = tmp_path / ".smart-organizer" / "history.jsonl"
    assert stats["moved"] == 1
    assert history_path.exists()
    record = json.loads(history_path.read_text(encoding="utf-8").splitlines()[0])
    assert record["schema_version"] == 1
    assert record["action"] == "move"

    undo_stats = undo_moves(str(tmp_path))

    assert undo_stats["restored"] == 1
    assert (tmp_path / "invoice.txt").exists()


def test_dry_run_does_not_write_history(tmp_path):
    config_path = _write_config(tmp_path)
    (tmp_path / "invoice.txt").write_text("invoice payment bank account tax revenue")

    FileOrganizer(str(tmp_path), dry_run=True, config_path=config_path).run()

    assert not (tmp_path / ".smart-organizer" / "history.jsonl").exists()


def test_undo_uses_collision_safe_restore_name(tmp_path):
    config_path = _write_config(tmp_path)
    (tmp_path / "invoice.txt").write_text("invoice payment bank account tax revenue")
    FileOrganizer(str(tmp_path), config_path=config_path).run()
    (tmp_path / "invoice.txt").write_text("new file occupying original path")

    stats = undo_moves(str(tmp_path))

    assert stats["restored"] == 1
    assert (tmp_path / "invoice_restored_1.txt").exists()


def test_smart_rename_records_rename_and_move_then_undo_restores_original(tmp_path, monkeypatch):
    config_path = _write_config(tmp_path)
    (tmp_path / "scan.txt").write_text("invoice payment bank account tax revenue")
    monkeypatch.setattr(SmartRenamer, "rename", lambda self, name, text: "Invoice_Acme.txt")

    FileOrganizer(str(tmp_path), smart_rename=True, api_key="x", config_path=config_path).run()

    records = OperationHistory.for_target(tmp_path).read_records()
    assert [record.action for record in records] == ["rename", "move"]

    stats = undo_moves(str(tmp_path))

    assert stats["restored"] == 2
    assert (tmp_path / "scan.txt").exists()
