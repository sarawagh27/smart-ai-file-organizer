"""Safety behaviour of live runs: renames, duplicates, scanning, --config."""

import json
from pathlib import Path

from smart_ai_file_organizer.history import OperationHistory
from smart_ai_file_organizer.organizer import FileOrganizer
from smart_ai_file_organizer.renamer import SmartRenamer
from smart_ai_file_organizer.undo import undo_moves
from smart_ai_file_organizer.utils import safe_move, scan_directory

INVOICE = "invoice payment bank account tax revenue"


def _config(tmp_path, **organizer):
    cfg = {
        "categories": ["Finance", "Other"],
        "training_data": {
            "Finance": [INVOICE],
            "Other": ["manual guide general notes"],
        },
        "organizer": {"supported_extensions": [".txt"], "fallback_category": "Other", **organizer},
        "corrections": [],
    }
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _target(tmp_path):
    target = tmp_path / "inbox"
    target.mkdir()
    return target


# -- Smart Rename -------------------------------------------------------------

def test_smart_rename_never_overwrites_existing_file(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "Finance").mkdir()
    (target / "Finance" / "Invoice_Acme.txt").write_text("PRECIOUS ORIGINAL")
    (target / "scan.txt").write_text(INVOICE)
    monkeypatch.setattr(SmartRenamer, "rename", lambda self, name, text: "Invoice_Acme.txt")

    FileOrganizer(str(target), smart_rename=True, api_key="x", config_path=cfg).run()

    assert (target / "Finance" / "Invoice_Acme.txt").read_text() == "PRECIOUS ORIGINAL"
    assert (target / "Finance" / "Invoice_Acme_1.txt").read_text() == INVOICE


def test_failed_move_leaves_file_with_its_original_name(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "scan.txt").write_text(INVOICE)
    monkeypatch.setattr(SmartRenamer, "rename", lambda self, name, text: "Invoice_Acme.txt")

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("smart_ai_file_organizer.organizer.safe_move", boom)
    stats = FileOrganizer(str(target), smart_rename=True, api_key="x", config_path=cfg).run()

    assert stats["errors"] == 1
    assert (target / "scan.txt").exists() and not (target / "Invoice_Acme.txt").exists()


def test_dry_run_never_calls_rename_api(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "scan.txt").write_text(INVOICE)
    calls = []
    monkeypatch.setattr(SmartRenamer, "rename", lambda self, name, text: calls.append(name) or name)

    FileOrganizer(str(target), dry_run=True, smart_rename=True, api_key="x", config_path=cfg).run()

    assert calls == []


# -- duplicates ---------------------------------------------------------------

def test_live_run_moves_duplicates_to_folder_and_undo_restores_them(tmp_path):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "a.txt").write_text(INVOICE)
    (target / "b.txt").write_text(INVOICE)

    org = FileOrganizer(str(target), config_path=cfg)
    stats = org.run()

    assert stats["duplicates"] == 1 and stats["moved"] == 1
    assert len(list((target / "_Duplicates").glob("*.txt"))) == 1
    assert len(org.duplicate_report) == 1
    assert not list(target.glob("*.txt"))

    undo_moves(str(target))
    assert sorted(p.name for p in target.glob("*.txt")) == ["a.txt", "b.txt"]


def test_duplicates_can_be_left_in_place(tmp_path):
    cfg = _config(tmp_path, duplicates_folder="")
    target = _target(tmp_path)
    (target / "a.txt").write_text(INVOICE)
    (target / "b.txt").write_text(INVOICE)

    stats = FileOrganizer(str(target), config_path=cfg).run()

    assert stats["duplicates"] == 1
    assert not (target / "_Duplicates").exists()
    assert len(list(target.glob("*.txt"))) == 1


def test_dry_run_reports_duplicates_without_moving(tmp_path):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "a.txt").write_text(INVOICE)
    (target / "b.txt").write_text(INVOICE)

    stats = FileOrganizer(str(target), dry_run=True, config_path=cfg).run()

    assert stats["duplicates"] == 1
    assert sorted(p.name for p in target.iterdir()) == ["a.txt", "b.txt"]


# -- scanning / --config ------------------------------------------------------

def test_scan_respects_custom_categories_extensions_and_hidden_folders(tmp_path):
    (tmp_path / "Invoices").mkdir()
    (tmp_path / "Invoices" / "done.txt").write_text("x")
    (tmp_path / "_Duplicates").mkdir()
    (tmp_path / "_Duplicates" / "dup.txt").write_text("x")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hidden.txt").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "keep.txt").write_text("x")
    (tmp_path / "top.txt").write_text("x")
    (tmp_path / "skip.pdf").write_text("x")

    found = scan_directory(
        str(tmp_path), recursive=True, categories=["Invoices"],
        extensions=[".txt"], skip_folders=["_Duplicates"],
    )

    assert sorted(Path(p).name for p in found) == ["keep.txt", "top.txt"]


def test_organizer_uses_custom_config_extensions(tmp_path):
    cfg = _config(tmp_path)          # only .txt supported
    target = _target(tmp_path)
    (target / "a.txt").write_text(INVOICE)
    (target / "b.csv").write_text(INVOICE + " different")

    stats = FileOrganizer(str(target), dry_run=True, config_path=cfg).run()

    assert stats["total_files"] == 1


def test_override_works_for_same_named_files_in_recursive_run(tmp_path):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    for sub, body in (("one", INVOICE), ("two", INVOICE + " second")):
        (target / sub).mkdir()
        (target / sub / "scan.txt").write_text(body)

    org = FileOrganizer(str(target), recursive=True, config_path=cfg)
    org.run()
    assert len(org.results) == 2
    names = [r[0] for r in org.results]
    assert len(set(names)) == 2                       # collision-safe names
    assert all(org.get_file_text(n) for n in names)   # text found for each


def test_safe_move_never_overwrites(tmp_path):
    (tmp_path / "src.txt").write_text("new")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "src.txt").write_text("old")

    moved = safe_move(str(tmp_path / "src.txt"), str(dest))

    assert (dest / "src.txt").read_text() == "old"
    assert moved.endswith("src_1.txt")


def test_history_records_move_for_duplicates(tmp_path):
    cfg = _config(tmp_path)
    target = _target(tmp_path)
    (target / "a.txt").write_text(INVOICE)
    (target / "b.txt").write_text(INVOICE)
    FileOrganizer(str(target), config_path=cfg).run()
    records = OperationHistory.for_target(target).read_records()
    assert [r.action for r in records] == ["move", "move"]
