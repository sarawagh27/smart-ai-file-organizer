from pathlib import Path

from smart_ai_file_organizer.history import OperationHistory
from smart_ai_file_organizer.undo import undo_moves


def test_undo_specific_run_id_only_restores_selected_run(tmp_path):
    history = OperationHistory.for_target(tmp_path)
    first_src = tmp_path / "first.txt"
    first_dest = tmp_path / "Finance" / "first.txt"
    second_src = tmp_path / "second.txt"
    second_dest = tmp_path / "Other" / "second.txt"
    first_dest.parent.mkdir()
    second_dest.parent.mkdir()
    first_dest.write_text("first")
    second_dest.write_text("second")
    history.record(run_id="run-1", action="move", source_path=first_src, destination_path=first_dest)
    history.record(run_id="run-2", action="move", source_path=second_src, destination_path=second_dest)

    stats = undo_moves(str(tmp_path), run_id="run-1")

    assert stats["restored"] == 1
    assert first_src.exists()
    assert second_dest.exists()


def test_undo_skips_file_changed_since_history_record(tmp_path):
    history = OperationHistory.for_target(tmp_path)
    source = tmp_path / "invoice.txt"
    dest = tmp_path / "Finance" / "invoice.txt"
    dest.parent.mkdir()
    dest.write_text("original")
    history.record(run_id="run-1", action="move", source_path=source, destination_path=dest)
    dest.write_text("changed")

    stats = undo_moves(str(tmp_path), run_id="run-1")

    assert stats["skipped"] == 1
    assert dest.exists()
    assert not source.exists()


def test_undo_ignores_broken_history_lines(tmp_path):
    history_path = tmp_path / ".smart-organizer" / "history.jsonl"
    history_path.parent.mkdir()
    history_path.write_text("{bad json}\n", encoding="utf-8")

    stats = undo_moves(str(tmp_path))

    assert stats == {"found": 0, "restored": 0, "skipped": 0, "errors": 0}


def test_undo_legacy_log_fallback_restores_file(tmp_path):
    dest = tmp_path / "Finance" / "invoice.txt"
    dest.parent.mkdir()
    dest.write_text("invoice")
    log = tmp_path / "organizer.log"
    log.write_text(f"INFO | utils | Moved 'invoice.txt' -> '{dest}'\n", encoding="utf-8")

    stats = undo_moves(str(tmp_path))

    assert stats["restored"] == 1
    assert (tmp_path / "invoice.txt").exists()
