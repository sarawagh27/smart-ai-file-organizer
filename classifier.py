"""
classifier.py
-------------
Trains and uses a TF-IDF + Naive Bayes document classifier.

New in Level 1:
  - predict_with_confidence() returns (category, confidence_pct, is_low_confidence)
  - add_correction() lets users manually override a classification
    and retrains the model immediately with the correction
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = Path(__file__).parent / "config.json"


def load_config(config_path: Path = DEFAULT_CONFIG) -> Dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class DocumentClassifier:
    """
    TF-IDF + Naive Bayes classifier driven by config.json.

    New methods
    -----------
    predict_with_confidence(text) → (category, confidence_pct, is_low)
    add_correction(text, correct_category) → retrains model immediately
    """

    def __init__(self, config_path: Path = DEFAULT_CONFIG):
        self.config = load_config(config_path)
        self.pipeline = None
        self._is_trained = False

        clf_cfg = self.config.get("classifier", {})
        self._confidence_threshold = clf_cfg.get("confidence_threshold", 0.20)
        self._ngram_range = tuple(clf_cfg.get("ngram_range", [1, 2]))
        self._nb_alpha = clf_cfg.get("naive_bayes_alpha", 0.5)

        org_cfg = self.config.get("organizer", {})
        self._fallback = org_cfg.get("fallback_category", "Other")

        # Build training corpus from config
        self._training_data: List[Tuple[str, str]] = []
        for label, samples in self.config.get("training_data", {}).items():
            for text in samples:
                self._training_data.append((text, label))

        # User corrections — stored separately, weighted x3 in retraining
        self._corrections: List[Tuple[str, str]] = []

        logger.debug(
            "Classifier loaded: %d categories, %d training samples.",
            len(self.config.get("categories", [])),
            len(self._training_data),
        )

    @property
    def categories(self) -> List[str]:
        return self.config.get("categories", ["Other"])

    def train(self) -> None:
        """Fit the pipeline on training data + any user corrections."""
        if not self._training_data:
            raise ValueError("No training data found in config.json.")

        # Combine base data with corrections (corrections repeated 3x for weight)
        all_data = self._training_data + self._corrections * 3
        texts  = [t for t, _ in all_data]
        labels = [l for _, l in all_data]

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=self._ngram_range,
                sublinear_tf=True,
                min_df=1,
                stop_words="english",
            )),
            ("clf", MultinomialNB(alpha=self._nb_alpha)),
        ])

        self.pipeline.fit(texts, labels)
        self._is_trained = True
        logger.info(
            "Classifier trained — %d samples (%d corrections) across %d categories.",
            len(texts), len(self._corrections), len(set(labels)),
        )

    def predict(self, text: str) -> str:
        """Return the predicted category label."""
        category, _, _ = self.predict_with_confidence(text)
        return category

    def predict_with_confidence(self, text: str) -> Tuple[str, float, bool]:
        """
        Classify text and return confidence information.

        Returns
        -------
        (category, confidence_pct, is_low_confidence)
          category         : predicted label
          confidence_pct   : 0–100 float (e.g. 87.3)
          is_low_confidence: True if model is uncertain (below threshold)
        """
        if not self._is_trained:
            raise RuntimeError("Call train() before predict().")

        if not text or not text.strip():
            logger.warning("Empty text — defaulting to '%s'.", self._fallback)
            return self._fallback, 0.0, True

        prediction   = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        confidence   = max(probabilities)
        confidence_pct = round(confidence * 100, 1)
        is_low       = confidence < self._confidence_threshold

        logger.debug(
            "Predicted '%s' (%.1f%% confidence%s)",
            prediction, confidence_pct,
            " — LOW" if is_low else "",
        )

        if is_low:
            return self._fallback, confidence_pct, True

        return prediction, confidence_pct, False

    def add_correction(self, text: str, correct_category: str) -> None:
        """
        Record a user correction and immediately retrain the model.

        Parameters
        ----------
        text             : the document text that was misclassified
        correct_category : the category the user says is correct
        """
        if correct_category not in self.categories:
            logger.warning(
                "Unknown category '%s' — correction ignored.", correct_category
            )
            return

        self._corrections.append((text, correct_category))
        logger.info(
            "Correction recorded: → '%s'. Retraining… (%d corrections total)",
            correct_category, len(self._corrections),
        )
        # Retrain immediately so next prediction benefits from the correction
        self.train()
