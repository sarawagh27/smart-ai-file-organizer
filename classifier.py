"""
classifier.py
-------------
Trains and uses a TF-IDF + Naive Bayes document classifier.

Categories and training data are loaded from config.json so users
can customise them without touching the source code.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Default config path — sits next to this file
DEFAULT_CONFIG = Path(__file__).parent / "config.json"


def load_config(config_path: Path = DEFAULT_CONFIG) -> Dict:
    """Load and return the parsed config.json."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Make sure config.json is in the project root."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class DocumentClassifier:
    """
    Wraps a scikit-learn TF-IDF → MultinomialNB pipeline.

    All categories, training data, and hyperparameters are driven
    by config.json — no code changes needed to customise.

    Usage
    -----
    clf = DocumentClassifier()
    clf.train()
    label = clf.predict("your document text here")
    """

    def __init__(self, config_path: Path = DEFAULT_CONFIG):
        self.config = load_config(config_path)
        self.pipeline = None
        self._is_trained = False

        # Pull settings from config
        clf_cfg = self.config.get("classifier", {})
        self._confidence_threshold = clf_cfg.get("confidence_threshold", 0.20)
        self._ngram_range = tuple(clf_cfg.get("ngram_range", [1, 2]))
        self._nb_alpha = clf_cfg.get("naive_bayes_alpha", 0.5)

        org_cfg = self.config.get("organizer", {})
        self._fallback = org_cfg.get("fallback_category", "Other")

        # Build flat training corpus from config
        self._training_data = []
        for label, samples in self.config.get("training_data", {}).items():
            for text in samples:
                self._training_data.append((text, label))

        logger.debug(
            "Classifier config loaded: %d categories, %d training samples.",
            len(self.config.get("categories", [])),
            len(self._training_data),
        )

    @property
    def categories(self) -> List[str]:
        """Return the list of category labels from config."""
        return self.config.get("categories", ["Other"])

    def train(self) -> None:
        """Build and fit the TF-IDF + Naive Bayes pipeline using config data."""
        if not self._training_data:
            raise ValueError("No training data found in config.json.")

        texts = [t for t, _ in self._training_data]
        labels = [l for _, l in self._training_data]

        self.pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=self._ngram_range,
                    sublinear_tf=True,
                    min_df=1,
                    stop_words="english",
                ),
            ),
            ("clf", MultinomialNB(alpha=self._nb_alpha)),
        ])

        self.pipeline.fit(texts, labels)
        self._is_trained = True
        logger.info(
            "Classifier trained — %d samples across %d categories.",
            len(texts), len(set(labels)),
        )

    def predict(self, text: str) -> str:
        """
        Classify a single document.

        Parameters
        ----------
        text : str  — extracted document text

        Returns
        -------
        str — category label from config.json
        """
        if not self._is_trained:
            raise RuntimeError("Call train() before predict().")

        if not text or not text.strip():
            logger.warning("Empty text — defaulting to '%s'.", self._fallback)
            return self._fallback

        prediction = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        confidence = max(probabilities)

        logger.debug("Predicted '%s' (confidence: %.1f%%)", prediction, confidence * 100)

        # Fall back when model is uncertain
        if confidence < self._confidence_threshold:
            logger.debug(
                "Low confidence (%.2f < %.2f) — returning '%s'.",
                confidence, self._confidence_threshold, self._fallback,
            )
            return self._fallback

        return prediction
