# Changelog

All notable changes to this project will be documented here.

## [0.2.0] - 2026-10-10

### Fixed

- Manual corrections now teach the transformer classifier immediately (previously only
  the TF-IDF fallback learned from them).
- The transformer classifier uses the config's `training_data`, so custom categories
  work. Previously only the 8 built-in categories had descriptions.
- Both classifier paths share one low-confidence policy (score threshold plus margin
  over the runner-up); low-confidence files go to the fallback category in both.
- Smart Rename can no longer overwrite an existing file, and a failed move no longer
  leaves a half-renamed file. Rename and move are now one step and one history entry.
- `--dry-run` no longer calls the NVIDIA API or sends any text off the machine.
- `--config` is respected when scanning: custom categories, extensions and the
  duplicates folder are skipped correctly on recursive re-runs. Hidden folders
  (`.git`, `.smart-organizer`) are skipped.
- Manual overrides work for same-named files in recursive runs.
- Categories returned by the TF-IDF model are plain `str`, not `numpy.str_`.

### Changed

- **Live runs now ask for confirmation** (`--yes` skips it; non-interactive sessions
  without `--yes` are refused). `--yes` previously did nothing.
- Duplicates are moved to `_Duplicates/` in live runs (recorded in history, so undo
  restores them). Set `organizer.duplicates_folder` to `""` for the old behavior.
- Semantic-search cache is JSON (`.search_index.json`) instead of pickle.
- PDF extraction uses `pypdf` (PyPDF2 is deprecated). `openai` moved to the optional
  `rename` extra.
- Default training data doubled (16 samples per category).
- Version bumped to 0.2.0.

### Added

- OCR fallback for scanned PDFs and images; Tesseract is found via `PATH`, then common
  install locations on Windows and macOS.
- Size and page caps in text extraction, and a bounded read for ZIP members.
- `scripts/evaluate_classifier.py` and 56 held-out labelled samples; accuracy test in CI.
- Tests for every extractor, the transformer logic (offline fake encoder), duplicate
  handling, rename safety, CLI confirmation, and the JSON cache. Coverage 66% to 76%.
- GitHub Actions: weekly/manual *AI model tests* with the real model, and a PyPI
  publish workflow (trusted publishing).
- `docs/LAUNCH_CHECKLIST.md` and `docs/media/social-preview.png`.

## Unreleased

### Added

- Testable category-management and watch-processing service layers that keep UI
  files thinner while preserving public commands.
- Coverage XML upload artifacts in GitHub Actions.
- Release checklist covering verification, demo refresh, changelog/versioning,
  and optional Windows executable packaging.
- Structured `.smart-organizer/history.jsonl` operation history with run ids,
  hashes, timestamps, action types, and source/destination paths.
- CLI options for `--config`, `--history`, `--run-id`, `--yes`, and `--version`.
- Architecture overview documenting runtime state, safety model, and testing
  strategy.
- Regression tests for config validation, CLI behavior, operation history,
  undo restore/collision handling, and search-cache invalidation.

### Changed

- Watch mode now delegates file filtering and move/history recording to a
  shared service with direct tests.
- Category Manager now delegates add/delete/update keyword rules to a shared
  service with direct tests.
- Undo now reads structured history first and uses `organizer.log` only as a
  legacy fallback.
- Semantic search cache now stores file size, mtime, and content hash metadata
  so changed files are reindexed and deleted files are dropped.
- Config loading is centralized and fails fast on invalid JSON or incomplete
  category/training-data settings.
- Coverage reporting now focuses on core logic while excluding interactive UI
  modules that need future adapter extraction.

### Security

- Undo verifies destination hashes before restoring files, reducing the risk of
  overwriting user changes made after an organize run.

## [0.1.0] - 2026-05-01

### Added

- Installable package metadata with console commands for CLI, GUI, undo, and watch mode.
- GitHub Actions CI for Python 3.10, 3.11, and 3.12.
- Security, contributing, changelog, roadmap, and issue/PR templates.
- Fast/offline test mode that avoids loading transformer models by default.
- Config fallback from private `config.json` to committed `config.example.json`.

### Changed

- Reworked README into a product-style GitHub landing page.
- Moved application code into the `smart_ai_file_organizer` package while keeping root wrappers.

### Fixed

- Duplicate detector summary now reports duplicate groups correctly.
- Semantic search now handles missing folders and empty queries cleanly.

### Security

- Removed committed private config and documented secret-handling expectations.
