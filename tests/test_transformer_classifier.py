"""Transformer classifier logic, tested offline with a tiny fake encoder."""

import re

import numpy as np

from smart_ai_file_organizer.classifier import DocumentClassifier, TransformerClassifier

VOCAB = [
    "invoice", "payment", "bank", "tax", "contract", "clause", "liability",
    "patient", "diagnosis", "dinosaur", "fossil", "jurassic", "bone", "museum",
]


class BagOfWordsEncoder:
    """Deterministic stand-in for sentence-transformers."""

    def encode(self, texts, normalize_embeddings=True, **_kwargs):
        rows = []
        for text in texts:
            words = re.findall(r"[a-z]+", text.lower())
            vec = np.array([words.count(w) for w in VOCAB], dtype=float)
            if normalize_embeddings and vec.any():
                vec = vec / np.linalg.norm(vec)
            rows.append(vec)
        return np.vstack(rows)


TRAINING = {
    "Finance": ["invoice payment bank"],
    "Legal": ["contract clause liability"],
    "Medical": ["patient diagnosis"],
    "Other": ["general notes"],
}
CATEGORIES = list(TRAINING)


def _loaded(categories=CATEGORIES, training=TRAINING):
    clf = TransformerClassifier(categories, training_data=training, model=BagOfWordsEncoder())
    assert clf.load()
    return clf


def test_predicts_closest_category_with_margin():
    category, score, margin = _loaded().predict("invoice payment due, bank transfer")
    assert category == "Finance"
    assert score > 0.5 and margin > 0.2


def test_custom_category_uses_config_training_data():
    training = {**TRAINING, "Paleontology": ["dinosaur fossil jurassic bone"]}
    clf = _loaded(list(training), training)
    category, _, _ = clf.predict("museum fossil bone from the jurassic")
    assert category == "Paleontology"


def test_add_example_changes_prediction_immediately():
    clf = _loaded()
    text = "dinosaur fossil museum"
    assert clf.predict(text)[1] == 0.0          # nothing similar is known yet
    clf.add_example(text, "Other")
    assert clf.predict("jurassic dinosaur fossil")[0] == "Other"


def _classifier_with_fake_transformer(corrections=None):
    clf = DocumentClassifier()
    clf._fallback = "Other"
    clf._corrections = list(corrections or [])
    transformer = _loaded()
    clf._transformer = transformer
    clf._use_transformer = True
    clf._is_trained = True
    return clf


def test_low_similarity_goes_to_fallback_like_tfidf_path():
    clf = _classifier_with_fake_transformer()
    category, _, is_low = clf.predict_with_confidence("dinosaur fossil museum")
    assert is_low and category == "Other"


def test_ambiguous_document_is_low_confidence_via_margin():
    clf = _classifier_with_fake_transformer()
    # Exactly as close to Finance as to Legal: similarity is high (~0.58) but the
    # margin is zero, so the prediction must not be trusted.
    category, confidence_pct, is_low = clf.predict_with_confidence("invoice payment contract clause")
    assert confidence_pct > 30 and is_low and category == "Other"


def test_add_correction_is_used_by_transformer(tmp_path, monkeypatch):
    clf = _classifier_with_fake_transformer()
    clf.config_path = tmp_path / "config.json"
    monkeypatch.setattr(clf, "_save_corrections", lambda: None)

    assert clf.predict_with_confidence("dinosaur fossil jurassic")[2] is True
    clf.add_correction("dinosaur fossil jurassic", "Medical")
    category, _, is_low = clf.predict_with_confidence("dinosaur fossil jurassic")
    assert category == "Medical" and not is_low
