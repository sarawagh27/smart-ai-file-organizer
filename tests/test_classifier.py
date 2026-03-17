"""
tests/test_classifier.py
------------------------
Unit tests for the DocumentClassifier.
"""

import sys
from pathlib import Path

import pytest

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier import DocumentClassifier, load_config


class TestLoadConfig:
    def test_config_loads_successfully(self):
        config = load_config()
        assert isinstance(config, dict)

    def test_config_has_categories(self):
        config = load_config()
        assert "categories" in config
        assert len(config["categories"]) > 0

    def test_config_has_training_data(self):
        config = load_config()
        assert "training_data" in config
        assert len(config["training_data"]) > 0


class TestDocumentClassifier:
    @pytest.fixture
    def trained_classifier(self):
        """Return a trained classifier instance."""
        clf = DocumentClassifier()
        clf.train()
        return clf

    def test_classifier_trains_without_error(self):
        clf = DocumentClassifier()
        clf.train()
        assert clf._is_trained is True

    def test_predict_raises_if_not_trained(self):
        clf = DocumentClassifier()
        with pytest.raises(RuntimeError, match="Call train()"):
            clf.predict("some text")

    def test_predict_returns_string(self, trained_classifier):
        result = trained_classifier.predict("invoice payment bank account tax")
        assert isinstance(result, str)

    def test_predict_returns_valid_category(self, trained_classifier):
        categories = trained_classifier.categories
        result = trained_classifier.predict("invoice payment bank account tax")
        assert result in categories

    def test_empty_text_returns_fallback(self, trained_classifier):
        result = trained_classifier.predict("")
        assert result == "Other"

    def test_whitespace_text_returns_fallback(self, trained_classifier):
        result = trained_classifier.predict("   ")
        assert result == "Other"

    @pytest.mark.parametrize("text,expected", [
        ("invoice payment bank balance tax revenue profit loss", "Finance"),
        ("resume skills python java experience university degree", "Resume"),
        ("neural network deep learning transformer BERT model training", "AI"),
        ("abstract hypothesis methodology experiment p-value statistical", "Research"),
        ("dear diary birthday family vacation memories friend", "Personal"),
        ("user manual installation guide troubleshooting FAQ setup", "Other"),
    ])
    def test_category_predictions(self, trained_classifier, text, expected):
        result = trained_classifier.predict(text)
        assert result == expected, f"Expected '{expected}' but got '{result}' for: {text[:50]}"

    def test_categories_property(self, trained_classifier):
        cats = trained_classifier.categories
        assert isinstance(cats, list)
        assert "Finance" in cats
        assert "Other" in cats
