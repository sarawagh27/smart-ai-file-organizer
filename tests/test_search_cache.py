from pathlib import Path

import pytest

from smart_ai_file_organizer.search import SemanticSearch


class FakeModel:
    def __init__(self):
        self.calls = 0

    def encode(self, texts, **_kwargs):
        self.calls += 1
        return [[1.0, 0.0] for _ in texts]


def test_search_cache_reuses_unchanged_entries_and_reindexes_changed_file(
    tmp_path, monkeypatch
):
    category = tmp_path / "Finance"
    category.mkdir()
    file_path = category / "invoice.txt"
    file_path.write_text("invoice payment bank", encoding="utf-8")
    model = FakeModel()

    monkeypatch.setattr(SemanticSearch, "_load_model", lambda self: setattr(self, "_model", model))

    engine = SemanticSearch(str(tmp_path))
    assert engine.build_index(force=True) == 1
    assert model.calls == 1

    engine2 = SemanticSearch(str(tmp_path))
    assert engine2.build_index() == 1
    assert model.calls == 1

    file_path.write_text("invoice payment bank updated", encoding="utf-8")
    engine3 = SemanticSearch(str(tmp_path))
    assert engine3.build_index() == 1
    assert model.calls == 2


def test_search_cache_drops_deleted_files(tmp_path, monkeypatch):
    category = tmp_path / "Finance"
    category.mkdir()
    file_path = category / "invoice.txt"
    file_path.write_text("invoice payment bank", encoding="utf-8")

    monkeypatch.setattr(
        SemanticSearch,
        "_load_model",
        lambda self: setattr(self, "_model", FakeModel()),
    )

    engine = SemanticSearch(str(tmp_path))
    assert engine.build_index(force=True) == 1
    file_path.unlink()

    engine2 = SemanticSearch(str(tmp_path))
    assert engine2.build_index() == 0
    assert engine2.index_size == 0
