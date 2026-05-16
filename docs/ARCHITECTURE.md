# Architecture

Smart AI File Organizer is a local-first Python application. Documents stay on
the user's machine unless the user explicitly enables Smart Rename with an
external NVIDIA/OpenAI-compatible API key.

## Core Flow

1. `main.py`, `gui.py`, `streamlit_app.py`, or `watcher.py` accepts files from a
   folder, upload, or filesystem event.
2. `text_extractor.py` extracts text from supported formats.
3. `classifier.py` classifies content with sentence-transformers when available,
   or a fast offline TF-IDF/Naive Bayes fallback.
4. `organizer.py` moves files into category folders and records every live
   rename/move in `.smart-organizer/history.jsonl`.
5. `undo.py` reverses the latest recorded run using structured history, with
   hash checks to avoid restoring files that changed after the original run.

## Runtime State

- `config.json`: private local settings, API keys, categories, and corrections.
- `config.example.json`: safe committed default configuration.
- `.smart-organizer/history.jsonl`: append-only structured operation history.
- `.search_index.pkl`: local semantic-search cache with file hash/mtime/size
  metadata for stale-entry detection.
- `organizer.log`: human-readable diagnostics only; undo no longer depends on it.

## Safety Model

- Dry-run mode never creates category folders, moves files, or writes history.
- Live mode records each operation before it can be undone later.
- Undo restores the latest run in reverse order and writes collision-safe
  filenames when the original path is already occupied.
- Config loading is centralized and validates malformed JSON, missing category
  lists, missing training data, and invalid extension settings.

## Testing Strategy

The core package is covered by unit and integration tests for classification,
organization, duplicate detection, text extraction, config validation, history,
undo, CLI behavior, and search-cache invalidation. Tkinter, Streamlit, and watch
mode are excluded from the coverage denominator until their business logic is
extracted behind testable adapters.
