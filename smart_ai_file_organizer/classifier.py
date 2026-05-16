"""
classifier.py
-------------
Level 2 — AI Upgrades:

  1. Better AI Model — sentence-transformers + cosine similarity
     Falls back to TF-IDF + Naive Bayes if not installed
  2. Permanent corrections — saved to config.json, survive restarts
  3. Language detection — detects document language before classifying

The model auto-selects:
  - If sentence-transformers installed → use it (higher accuracy)
  - If not installed         → fall back to TF-IDF + Naive Bayes
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from .config import DEFAULT_CONFIG, EXAMPLE_CONFIG, load_config, save_config

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


# ── Language detection ───────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect the language of a text string.

    Returns ISO 639-1 code (e.g. 'en', 'hi', 'fr', 'ar') or 'unknown'.
    Requires: pip install langdetect
    """
    if not text or len(text.strip()) < 20:
        return "unknown"
    try:
        from langdetect import detect, LangDetectException
        return detect(text)
    except Exception:
        return "unknown"


LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "ar": "Arabic",
    "fr": "French",  "de": "German", "es": "Spanish", "zh": "Chinese",
    "ja": "Japanese","pt": "Portuguese", "ru": "Russian", "it": "Italian",
    "ko": "Korean",  "nl": "Dutch", "tr": "Turkish", "pl": "Polish",
    "unknown": "Unknown",
}


# ── Sentence-Transformers classifier ────────────────────────────────────────

class TransformerClassifier:
    """
    Uses sentence-transformers to embed documents and category descriptions,
    then picks the closest category by cosine similarity.

    This approach needs ZERO labelled training data — it understands meaning.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"   # 90MB, fast, accurate

    def __init__(self, categories: List[str]):
        self.categories = categories
        self._model     = None
        self._cat_embeddings = None

        # Human-readable descriptions for each category
        # The model matches document text against these descriptions
        self._descriptions = {
            "Finance":  "invoice payment bank account balance tax revenue profit loss budget financial statement earnings dividend mortgage loan credit debit",
            "Resume":   "resume curriculum vitae work experience education skills objective summary references degree university employment history linkedin cover letter",
            "AI":       "artificial intelligence machine learning deep learning neural network model training dataset transformer BERT GPT computer vision NLP",
            "Research": "abstract introduction methodology results conclusion hypothesis experiment statistical analysis peer reviewed journal publication thesis dissertation",
            "Personal": "diary journal letter family friend birthday vacation holiday memories feelings thoughts gratitude personal reflection",
            "Legal":    "contract agreement terms conditions clause liability warranty jurisdiction attorney court plaintiff defendant NDA lease employment",
            "Medical":  "patient diagnosis treatment prescription medication symptoms clinical lab results blood test hospital doctor nurse insurance health",
            "Other":    "manual guide instructions meeting agenda news article recipe product description general information",
        }

    def load(self) -> bool:
        """Load the sentence-transformers model. Returns True on success."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            logger.info("Loading sentence-transformers model '%s'…", self.MODEL_NAME)
            self._model = SentenceTransformer(self.MODEL_NAME)

            # Pre-embed category descriptions
            descs = [self._descriptions.get(cat, cat) for cat in self.categories]
            self._cat_embeddings = self._model.encode(descs, normalize_embeddings=True)
            logger.info("sentence-transformers model ready ✓")
            return True
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers  to enable the better model."
            )
            return False
        except Exception as e:
            logger.warning("Failed to load transformer model: %s", e)
            return False

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Returns (category, confidence_pct).
        Confidence = cosine similarity × 100.
        """
        import numpy as np
        # Truncate to first 512 words for speed
        snippet = " ".join(text.split()[:512])
        doc_emb = self._model.encode([snippet], normalize_embeddings=True)
        sims    = (doc_emb @ self._cat_embeddings.T)[0]
        best_i  = int(np.argmax(sims))
        return self.categories[best_i], round(float(sims[best_i]) * 100, 1)


# ── Main DocumentClassifier ──────────────────────────────────────────────────

class DocumentClassifier:
    """
    Smart classifier with automatic model selection:
      - Uses sentence-transformers if available (Level 2)
      - Falls back to TF-IDF + Naive Bayes (Level 1)

    Level 2 additions:
      - detect_language() called on every document
      - Corrections saved permanently to config.json
    """

    def __init__(self, config_path: Path | str | None = None):
        self.config_path = config_path
        self.config      = load_config(config_path)
        self._is_trained = False

        # TF-IDF pipeline (fallback)
        self.pipeline: Optional[Pipeline] = None

        # Transformer model (primary)
        self._transformer: Optional[TransformerClassifier] = None
        self._use_transformer = False

        clf_cfg = self.config.get("classifier", {})
        self._confidence_threshold = clf_cfg.get("confidence_threshold", 0.18)
        self._ngram_range  = tuple(clf_cfg.get("ngram_range", [1, 2]))
        self._nb_alpha     = clf_cfg.get("naive_bayes_alpha", 0.4)

        org_cfg = self.config.get("organizer", {})
        self._fallback = org_cfg.get("fallback_category", "Other")

        # Build base training corpus
        self._training_data: List[Tuple[str, str]] = []
        for label, samples in self.config.get("training_data", {}).items():
            for text in samples:
                self._training_data.append((text, label))

        # Load saved corrections from config
        self._corrections: List[Tuple[str, str]] = [
            (c["text"], c["category"])
            for c in self.config.get("corrections", [])
        ]

        logger.debug(
            "Classifier loaded: %d categories, %d samples, %d saved corrections.",
            len(self.categories), len(self._training_data), len(self._corrections),
        )

    @property
    def categories(self) -> List[str]:
        return self.config.get("categories", ["Other"])

    @property
    def model_name(self) -> str:
        return "sentence-transformers" if self._use_transformer else "TF-IDF + Naive Bayes"

    def train(self) -> None:
        """Try to load transformer model; fall back to TF-IDF if unavailable."""
        disable_transformers = os.environ.get(
            "SMART_ORGANIZER_DISABLE_TRANSFORMERS", ""
        ).lower() in {"1", "true", "yes", "on"}

        # Try transformer first unless fast/offline mode is requested.
        transformer = TransformerClassifier(self.categories)
        if not disable_transformers and transformer.load():
            self._transformer     = transformer
            self._use_transformer = True
            self._is_trained      = True
            logger.info("Using sentence-transformers model ✓")
        else:
            # Fall back to TF-IDF + Naive Bayes
            self._train_tfidf()
            logger.info("Using TF-IDF + Naive Bayes model ✓")

        self._is_trained = True

    def _train_tfidf(self) -> None:
        all_data = self._training_data + self._corrections * 3
        texts    = [t for t, _ in all_data]
        labels   = [l for _, l in all_data]

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=self._ngram_range,
                sublinear_tf=True, min_df=1, stop_words="english",
            )),
            ("clf", MultinomialNB(alpha=self._nb_alpha)),
        ])
        self.pipeline.fit(texts, labels)
        logger.info(
            "TF-IDF classifier trained — %d samples, %d corrections.",
            len(texts), len(self._corrections),
        )

    def predict(self, text: str) -> str:
        category, _, _ = self.predict_with_confidence(text)
        return category

    def predict_with_confidence(self, text: str) -> Tuple[str, float, bool]:
        """
        Returns (category, confidence_pct, is_low_confidence).
        Also logs the detected language.
        """
        if not self._is_trained:
            raise RuntimeError("Call train() before predict().")

        if not text or not text.strip():
            return self._fallback, 0.0, True

        # Detect language
        lang_code = detect_language(text)
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)
        if lang_code not in ("en", "unknown"):
            logger.info("  🌐 Language detected: %s (%s)", lang_name, lang_code)

        # Classify
        if self._use_transformer and self._transformer:
            category, confidence_pct = self._transformer.predict(text)
            # Transformer similarity scores are lower than NB probabilities
            # Threshold is 30% similarity for transformers
            is_low = (confidence_pct / 100) < 0.30
        else:
            prediction    = self.pipeline.predict([text])[0]
            probabilities = self.pipeline.predict_proba([text])[0]
            confidence    = max(probabilities)
            confidence_pct = round(confidence * 100, 1)
            is_low         = confidence < self._confidence_threshold
            category       = prediction if not is_low else self._fallback

        logger.debug(
            "Predicted '%s' (%.1f%% | %s%s)",
            category, confidence_pct, self.model_name,
            " — LOW" if is_low else "",
        )

        return category, confidence_pct, is_low

    def add_correction(self, text: str, correct_category: str) -> None:
        """
        Record a correction, retrain immediately, and save permanently to config.json.
        """
        if correct_category not in self.categories:
            logger.warning("Unknown category '%s' — ignored.", correct_category)
            return

        self._corrections.append((text, correct_category))
        logger.info(
            "Correction saved: → '%s' (%d total). Retraining…",
            correct_category, len(self._corrections),
        )

        # Save to config.json permanently
        self._save_corrections()

        # Retrain
        if self._use_transformer:
            pass  # Transformer doesn't need retraining
        else:
            self._train_tfidf()

    def _save_corrections(self) -> None:
        """Persist corrections to config.json so they survive restarts."""
        try:
            self.config["corrections"] = [
                {"text": text[:500], "category": cat}   # cap text length
                for text, cat in self._corrections
            ]
            save_config(self.config, self.config_path)
            logger.debug("Corrections saved to config.json (%d total).", len(self._corrections))
        except Exception as e:
            logger.error("Failed to save corrections: %s", e)
