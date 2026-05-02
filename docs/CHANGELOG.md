# Changelog

All notable changes to this project will be documented here.

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
