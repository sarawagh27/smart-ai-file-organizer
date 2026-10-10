"""
classifier.py
-------------
Document classification with two interchangeable back ends:

  1. Transformer (sentence-transformers) — nearest-exemplar matching.
     Every labelled example (config ``training_data``, built-in category
     descriptions, and the user's saved corrections) is embedded once; a
     document is assigned to the category of its most similar exemplar.
     Corrections therefore take effect immediately, and custom categories
     work as soon as they have training samples.
  2. TF-IDF + Multinomial Naive Bayes — fast, offline fallback.

Both back ends share one low-confidence policy: a prediction is "low
confidence" when the top score is below the threshold *or* the gap to the
runner-up category (the margin) is too small. Low-confidence documents are
sent to the fallback category ("Other") and flagged for review.

Corrections are saved to config.json, so they survive restarts.
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

# Built-in descriptions for the default categories. They are used as one extra
# exemplar per category; custom categories rely on their config training data.
DEFAULT_DESCRIPTIONS: Dict[str, str] = {
    "Finance":  "invoice payment bank account balance tax revenue profit loss budget financial statement earnings dividend mortgage loan credit debit",
    "Resume":   "resume curriculum vitae work experience education skills objective summary references degree university employment history linkedin cover letter",
    "AI":       "artificial intelligence machine learning deep learning neural network model training dataset transformer BERT GPT computer vision NLP",
    "Research": "abstract introduction methodology results conclusion hypothesis experiment statistical analysis peer reviewed journal publication thesis dissertation",
    "Personal": "diary journal letter family friend birthday vacation holiday memories feelings thoughts gratitude personal reflection",
    "Legal":    "contract agreement terms conditions clause liability warranty jurisdiction attorney court plaintiff defendant NDA lease employment",
    "Medical":  "patient diagnosis treatment prescription medication symptoms clinical lab results blood test hospital doctor nurse insurance health",
    "Other":    "manual guide instructions meeting agenda news article recipe product description general information",
}


class TransformerClassifier:
    """
    Nearest-exemplar classifier on top of sentence-transformers embeddings.

    Needs no training step: each category is represented by the embeddings of
    its labelled examples, and a document gets the category of the most
    similar example. ``add_example`` lets corrections join the pool live.

    Parameters
    ----------
    categories    : category names, in config order
    training_data : {category: [example text, ...]} from the config
    model         : optional pre-built encoder (anything with ``encode``);
                    used by tests to avoid downloading a model
    """

    MODEL_NAME = "all-MiniLM-L6-v2"   # ~90MB, fast, accurate

    def __init__(
        self,
        categories: List[str],
        training_data: Optional[Dict[str, List[str]]] = None,
        model=None,
    ):
        self.categories = list(categories)
        self.training_data = training_data or {}
        self._model = model
        self._exemplar_embeddings = None          # (n_exemplars, dim) ndarray
        self._exemplar_categories: List[str] = []

    # -- setup ---------------------------------------------------------------
    def _exemplars(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for cat in self.categories:
            samples = [t for t in self.training_data.get(cat, []) if t and t.strip()]
            description = DEFAULT_DESCRIPTIONS.get(cat)
            if description:
                samples.append(description)
            if not samples:
                samples = [cat]          # last resort: the category name itself
            pairs.extend((text, cat) for text in samples)
        return pairs

    def load(self) -> bool:
        """Load the model (if needed) and embed all exemplars. True on success."""
        try:
            import numpy as np  # noqa: F401

            if self._model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence-transformers model '%s'…", self.MODEL_NAME)
                self._model = SentenceTransformer(self.MODEL_NAME)

            pairs = self._exemplars()
            self._exemplar_categories = [cat for _, cat in pairs]
            self._exemplar_embeddings = self._encode([text for text, _ in pairs])
            logger.info(
                "sentence-transformers ready ✓ (%d exemplars, %d categories)",
                len(pairs), len(self.categories),
            )
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

    def _encode(self, texts: List[str]):
        import numpy as np
        snippets = [" ".join(t.split()[:512]) for t in texts]
        emb = self._model.encode(snippets, normalize_embeddings=True)
        return np.asarray(emb, dtype=float).reshape(len(snippets), -1)

    def add_example(self, text: str, category: str) -> None:
        """Add one labelled example (e.g. a user correction) to the pool."""
        import numpy as np
        if self._exemplar_embeddings is None:
            raise RuntimeError("Call load() before add_example().")
        vec = self._encode([text])
        self._exemplar_embeddings = np.vstack([self._exemplar_embeddings, vec])
        self._exemplar_categories.append(category)

    # -- inference -----------------------------------------------------------
    def predict(self, text: str) -> Tuple[str, float, float]:
        """
        Returns (category, score, margin) with score and margin in 0-1.

        score  = cosine similarity of the closest exemplar
        margin = score minus the best score of any *other* category
        """
        import numpy as np
        if self._exemplar_embeddings is None:
            raise RuntimeError("Call load() before predict().")

        doc = self._encode([text])[0]
        sims = self._exemplar_embeddings @ doc

        best_per_cat: Dict[str, float] = {}
        for sim, cat in zip(sims, self._exemplar_categories):
            if sim > best_per_cat.get(cat, -2.0):
                best_per_cat[cat] = float(sim)

        ranked = sorted(best_per_cat.items(), key=lambda kv: kv[1], reverse=True)
        best_cat, best_score = ranked[0]
        margin = best_score - ranked[1][1] if len(ranked) > 1 else best_score
        return best_cat, float(np.clip(best_score, 0.0, 1.0)), float(max(margin, 0.0))


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
        self._transformer_threshold = clf_cfg.get("transformer_confidence_threshold", 0.30)
        self._min_margin = clf_cfg.get("min_margin", 0.02)
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
        transformer = TransformerClassifier(
            self.categories, training_data=self.config.get("training_data", {}),
        )
        if not disable_transformers and transformer.load():
            for text, label in self._corrections:   # saved corrections apply at once
                if label in self.categories:
                    transformer.add_example(text, label)
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

        # Classify — both back ends feed the same low-confidence policy
        if self._use_transformer and self._transformer:
            category, score, margin = self._transformer.predict(text)
            threshold = self._transformer_threshold
        else:
            probabilities = self.pipeline.predict_proba([text])[0]
            ranked = sorted(zip(self.pipeline.classes_, probabilities), key=lambda kv: kv[1], reverse=True)
            category, score = str(ranked[0][0]), float(ranked[0][1])
            margin = score - float(ranked[1][1]) if len(ranked) > 1 else score
            threshold = self._confidence_threshold

        is_low = score < threshold or margin < self._min_margin
        if is_low:
            category = self._fallback
        confidence_pct = round(score * 100, 1)

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

        # Apply immediately: the transformer just gains one more exemplar,
        # the TF-IDF model is retrained.
        if self._use_transformer and self._transformer:
            self._transformer.add_example(text, correct_category)
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
