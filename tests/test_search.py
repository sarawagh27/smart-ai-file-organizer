"""
tests/test_search.py
--------------------
Tests for the SemanticSearch engine.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

skip_no_st = pytest.mark.skipif(
    not HAS_SENTENCE_TRANSFORMERS,
    reason="sentence-transformers not installed"
)

ROOT = Path(__file__).parent.parent


def _make_organised_folder(base: Path, categories_and_files: dict) -> None:
    """Create a mock organised folder with category sub-folders."""
    for category, files in categories_and_files.items():
        cat_dir = base / category
        cat_dir.mkdir(parents=True)
        for fname, content in files.items():
            (cat_dir / fname).write_text(content, encoding="utf-8")


@pytest.fixture
def organised_folder(tmp_path):
    """Create a realistic organised folder for testing."""
    import sys
    sys.path.insert(0, str(ROOT))

    # Copy config
    shutil.copy(ROOT / "config.example.json", tmp_path / "config.json")

    # Create mock organised files
    _make_organised_folder(tmp_path, {
        "Finance": {
            "invoice_amazon.txt": "Invoice #1234 payment Amazon order total amount $500 tax revenue bank account balance due",
            "budget_2024.txt":    "Annual budget spreadsheet revenue expenses profit loss financial planning quarterly earnings",
        },
        "Medical": {
            "blood_test.txt":    "Patient blood test results hemoglobin CBC cholesterol glucose blood pressure diagnosis treatment",
            "prescription.txt":  "Prescription medication dosage doctor hospital patient symptoms clinical notes",
        },
        "AI": {
            "ml_notes.txt":      "Machine learning neural network deep learning transformer model training dataset accuracy loss",
            "research_paper.txt":"Natural language processing BERT GPT attention mechanism tokenization embedding classification",
        },
        "Other": {
            "readme.txt": "Installation guide setup configuration system requirements steps procedure manual",
        }
    })
    return tmp_path


class TestSemanticSearch:

    def test_import(self):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        assert SemanticSearch is not None

    def test_init(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        assert engine.index_size == 0
        assert not engine._is_built

    @skip_no_st
    def test_build_index(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        n = engine.build_index()
        assert n == 7
        assert engine._is_built
        assert engine.index_size == 7

    @skip_no_st
    def test_search_finance(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("invoice payment bank")
        assert len(results) > 0
        top = results[0]
        assert top[1] == "Finance"   # category
        assert top[2] > 0            # confidence > 0

    @skip_no_st
    def test_search_medical(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("blood test medical report")
        assert len(results) > 0
        categories = [r[1] for r in results[:3]]
        assert "Medical" in categories

    @skip_no_st
    def test_search_with_category_filter(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("document", category_filter="Finance")
        for _, cat, _, _, _ in results:
            assert cat == "Finance"

    @skip_no_st
    def test_search_returns_sorted_by_score(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("machine learning neural network")
        scores = [r[2] for r in results]
        assert scores == sorted(scores, reverse=True)

    @skip_no_st
    def test_search_empty_query_returns_empty(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("xyzzy123nonexistent", min_score=0.99)
        assert results == []

    @skip_no_st
    def test_index_cached(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        cache = organised_folder / ".search_index.pkl"
        assert cache.exists()

        # Second load uses cache
        engine2 = SemanticSearch(target_dir=str(organised_folder))
        n = engine2.build_index()
        assert n == 7

    @skip_no_st
    def test_clear_cache(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        engine.clear_cache()
        assert not engine._is_built
        assert engine.index_size == 0
        cache = organised_folder / ".search_index.pkl"
        assert not cache.exists()

    @skip_no_st
    def test_force_rebuild(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        n = engine.build_index(force=True)
        assert n == 7

    @skip_no_st
    def test_result_structure(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("invoice")
        if results:
            fname, category, score, preview, path = results[0]
            assert isinstance(fname, str)
            assert isinstance(category, str)
            assert isinstance(score, float)
            assert isinstance(preview, str)
            assert isinstance(path, str)
            assert 0 <= score <= 100

    @skip_no_st
    def test_top_k_limit(self, organised_folder):
        import sys
        sys.path.insert(0, str(ROOT))
        from search import SemanticSearch
        engine = SemanticSearch(target_dir=str(organised_folder))
        engine.build_index()
        results = engine.search("document file text", top_k=3, min_score=0.0)
        assert len(results) <= 3
