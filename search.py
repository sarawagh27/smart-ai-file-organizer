"""
search.py
---------
Semantic Search for Smart AI File Organizer.

Uses sentence-transformers to build an index of all organized files
and search them by meaning — not just keywords.

How it works
------------
1. Scan all category subfolders for organized files
2. Extract text from each file
3. Encode each file as a 384-dim embedding vector
4. On search: encode the query, find closest files by cosine similarity
5. Return ranked results with similarity scores

Usage
-----
    from search import SemanticSearch
    engine = SemanticSearch(target_dir="D:/Downloads")
    engine.build_index()
    results = engine.search("medical reports blood test")
    # Returns: [(filename, category, score, preview), ...]
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pickle

logger = logging.getLogger(__name__)

# Cache file to avoid re-indexing every time
INDEX_FILE = ".search_index.pkl"


class SemanticSearch:
    """
    Semantic search engine for organized files.

    Parameters
    ----------
    target_dir : str — the organized folder (contains category subfolders)
    """

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        self._model        = None
        self._index        = []   # list of dicts: {path, category, text, embedding}
        self._is_built     = False

    # ── Model ────────────────────────────────────────────────────────────────
    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Semantic search model loaded ✓")
            except ImportError:
                raise ImportError(
                    "sentence-transformers required for semantic search.\n"
                    "Run: pip install sentence-transformers"
                )

    # ── Build index ──────────────────────────────────────────────────────────
    def build_index(self, force: bool = False) -> int:
        """
        Scan all category subfolders, extract text, build embeddings.

        Parameters
        ----------
        force : bool — if True, rebuild even if cache exists

        Returns
        -------
        int — number of files indexed
        """
        from text_extractor import extract_text, SUPPORTED_EXTENSIONS

        if not self.target_dir.exists() or not self.target_dir.is_dir():
            logger.warning(
                "Search target does not exist or is not a folder: %s",
                self.target_dir,
            )
            self._index = []
            self._is_built = False
            return 0

        # Load config for categories
        config_path = Path(__file__).parent / "config.json"
        if not config_path.exists():
            config_path = Path(__file__).parent / "config.example.json"

        try:
            with open(config_path) as f:
                cfg = json.load(f)
            categories = cfg.get("categories", [])
        except Exception:
            categories = []

        # Try loading cached index
        cache_path = self.target_dir / INDEX_FILE
        if not force and cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    cached = pickle.load(f)
                self._index    = cached["index"]
                self._is_built = True
                logger.info("Loaded cached search index (%d files)", len(self._index))
                return len(self._index)
            except Exception:
                pass

        self._load_model()
        self._index = []

        # Scan category subfolders
        files_found = []
        for cat_dir in self.target_dir.iterdir():
            if cat_dir.is_dir() and cat_dir.name in categories:
                for f in cat_dir.rglob("*"):
                    if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files_found.append((f, cat_dir.name))

        if not files_found:
            logger.warning("No indexed files found in %s", self.target_dir)
            return 0

        logger.info("Building search index for %d files…", len(files_found))

        texts      = []
        meta_items = []

        for filepath, category in files_found:
            try:
                text = extract_text(str(filepath))
                if not text.strip():
                    continue
                snippet = " ".join(text.split()[:300])
                texts.append(snippet)
                preview = " ".join(text.split()[:60])
                meta_items.append({
                    "path":     str(filepath),
                    "filename": filepath.name,
                    "category": category,
                    "preview":  preview,
                })
            except Exception as exc:
                logger.warning("Skipping %s: %s", filepath.name, exc)

        if not texts:
            return 0

        # Batch encode all texts
        import numpy as np
        embeddings = self._model.encode(
            texts, normalize_embeddings=True,
            show_progress_bar=False, batch_size=32,
        )

        for meta, emb in zip(meta_items, embeddings):
            meta["embedding"] = emb
            self._index.append(meta)

        # Save cache
        try:
            with open(cache_path, "wb") as f:
                pickle.dump({"index": self._index}, f)
            logger.info("Search index built and cached (%d files)", len(self._index))
        except Exception as e:
            logger.warning("Could not cache index: %s", e)

        self._is_built = True
        return len(self._index)

    # ── Search ───────────────────────────────────────────────────────────────
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.25,
        category_filter: Optional[str] = None,
    ) -> List[Tuple[str, str, float, str]]:
        """
        Search for files semantically similar to the query.

        Parameters
        ----------
        query           : natural language search query
        top_k           : max number of results to return
        min_score       : minimum similarity score (0-1)
        category_filter : optional — only return files from this category

        Returns
        -------
        List of (filename, category, score_pct, preview)
        """
        if not query or not query.strip():
            return []

        if not self._is_built or not self._index:
            logger.warning("Index not built. Call build_index() first.")
            return []

        self._load_model()

        import numpy as np

        query_emb = self._model.encode([query], normalize_embeddings=True)[0]

        scores = []
        for item in self._index:
            if category_filter and item["category"] != category_filter:
                continue
            score = float(np.dot(query_emb, item["embedding"]))
            if score >= min_score:
                scores.append((item["filename"], item["category"],
                                round(score * 100, 1), item["preview"],
                                item["path"]))

        # Sort by score descending
        scores.sort(key=lambda x: x[2], reverse=True)
        return scores[:top_k]

    def clear_cache(self):
        """Delete the cached index so it rebuilds on next call."""
        cache_path = self.target_dir / INDEX_FILE
        if cache_path.exists():
            cache_path.unlink()
        self._index    = []
        self._is_built = False
        logger.info("Search index cache cleared.")

    @property
    def index_size(self) -> int:
        return len(self._index)
