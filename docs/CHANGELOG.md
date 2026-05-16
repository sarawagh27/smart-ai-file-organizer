# Changelog

All notable changes to this project will be documented here.

## Unreleased

### Added

- Structured `.smart-organizer/history.jsonl` operation history with run ids,
  hashes, timestamps, action types, and source/destination paths.
- CLI options for `--config`, `--history`, `--run-id`, `--yes`, and `--version`.
- Architecture overview documenting runtime state, safety model, and testing
  strategy.
- Regression tests for config validation, CLI behavior, operation history,
  undo restore/collision handling, and search-cache invalidation.

### Changed

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
