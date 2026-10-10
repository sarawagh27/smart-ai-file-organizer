# Smart AI File Organizer

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge">
  <img alt="Status Beta" src="https://img.shields.io/badge/Status-Beta-f59e0b?style=for-the-badge">
  <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/sarawagh27/smart-ai-file-organizer/ci.yml?branch=main&style=for-the-badge&label=CI">
  <a href="https://smart-ai-file-organizer.streamlit.app">
    <img alt="Live Demo" src="https://img.shields.io/badge/Live%20Demo-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white">
  </a>
</p>

<p align="center">
  <strong>AI-powered file organization for messy local folders.</strong><br>
  Classify, rename, deduplicate, and search documents by what they contain, not what they are called.<br>
  Use it from the CLI, desktop GUI, or Streamlit web app.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#interfaces">Interfaces</a> &middot;
  <a href="#demo">Demo</a> &middot;
  <a href="#usage">Usage</a> &middot;
  <a href="docs/ROADMAP.md">Roadmap</a>
</p>

## Why This Project?

Most folders become messy because filenames are unreliable: `scan_001.pdf`,
`final_final.docx`, exported spreadsheets, duplicated downloads, and screenshots
all pile up together.

Smart AI File Organizer reads the content inside each file, then gives you a
safer workflow for turning chaos into structure:

- Preview every move with dry-run mode before touching files.
- Undo live runs from structured local history instead of fragile log parsing.
- Classify documents by meaning using transformer embeddings or a fast offline
  TF-IDF fallback.
- Detect duplicates by content hash instead of filename.
- Search organized files semantically, even when you do not remember exact words.
- Keep secrets and personal category rules in local config, outside git.

## Demo

![Smart AI File Organizer demo](docs/media/demo.gif)

The demo GIF is captured from the real Streamlit app. It shows file upload,
text classification, result export, semantic search, and category management
screens.

Screenshot capture targets for the CLI safety flow and desktop GUI are tracked
in [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) so release demos
stay tied to verified behavior.

## Safety Demo

```bash
smart-organizer ~/Downloads --dry-run   # preview: nothing moves, no API calls
smart-organizer ~/Downloads             # live run: asks for confirmation first
smart-organizer ~/Downloads --yes       # live run without the prompt (scripts, cron)
smart-organizer ~/Downloads --undo
```

Paths are shown Unix-style; on Windows use `D:\Downloads` or any folder you like.
A live run in a non-interactive session (pipe, cron, CI) is refused unless you pass
`--yes`, so files are never moved by accident.

Live runs write structured history to
`~/Downloads/.smart-organizer/history.jsonl`. Undo restores the latest run from
that history and skips files whose contents changed after organization.

## Before vs After

```text
Before: Downloads/                 After: Downloads/
|-- scan_001.pdf                   |-- Finance/
|-- final_final.docx               |   `-- budget_march.xlsx
|-- notes.txt                      |-- Resume/
|-- report-copy.pdf                |   `-- final_final.docx
|-- IMG_2044.jpg                   |-- Research/
`-- budget_march.xlsx              |   `-- report-copy.pdf
                                   |-- Personal/
                                   |   `-- IMG_2044.jpg
                                   |-- Other/
                                   |   `-- notes.txt
                                   `-- organizer.log
```

With Smart Rename enabled, vague names can become descriptive:

```text
scan0023.pdf       -> Invoice_Amazon_Mar2024_1299.pdf
doc_final_v3.docx  -> Resume_Software_Engineer_2026.docx
untitled_notes.txt -> AI_Transformer_Research_Notes.txt
```

## Features

- Content-aware document classification.
- TXT, CSV, PDF, DOCX, XLSX, PPTX, EML, MSG, ZIP, PNG, JPG, and JPEG support.
- Duplicate detection with content hashes. Live runs move duplicates into a
  `_Duplicates/` folder (undo-able); set `organizer.duplicates_folder` to `""`
  to leave them in place.
- OCR fallback for scanned PDFs and images (optional `ocr` extra + Tesseract).
- Semantic search across organized folders.
- Dry-run, undo, recursive scan, watch mode, and operation logs.
- Category management, manual overrides, confidence scores, and exports.
- Optional NVIDIA-powered Smart Rename.

## Interfaces

| Interface | Best For | Command |
| --- | --- | --- |
| CLI | Fast local automation and dry runs | `smart-organizer ~/Downloads --dry-run` |
| Desktop GUI | Reviewable interactive organization | `smart-organizer-gui` |
| Streamlit | Browser-based demo and uploads | `streamlit run streamlit_app.py` |
| Watch Mode | Continuous folder monitoring | `smart-organizer-watch ~/Downloads` |

## Quick Start

```bash
git clone https://github.com/sarawagh27/smart-ai-file-organizer.git
cd smart-ai-file-organizer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Install optional AI, web, and OCR extras only when needed:

```bash
python -m pip install -e ".[ai,web]"   # transformer model + Streamlit app
python -m pip install -e ".[ocr]"      # scanned PDFs and images (needs Tesseract)
python -m pip install -e ".[rename]"   # Smart Rename (openai client)
```

`pyproject.toml` is the canonical dependency manifest. `requirements.txt` is
kept only as a small deployment fallback for platforms that expect it.

## Usage

Preview organization without moving files:

```bash
smart-organizer ~/Downloads --dry-run
```

Organize a folder:

```bash
smart-organizer ~/Downloads --yes
```

Include subfolders:

```bash
smart-organizer ~/Downloads --recursive
```

Enable AI-powered filenames:

```bash
smart-organizer ~/Downloads --smart-rename
```

Undo the last run:

```bash
smart-organizer-undo ~/Downloads
```

Use custom config/history paths for demos or tests:

```bash
smart-organizer ~/Downloads --dry-run --config ./config.example.json
smart-organizer ~/Downloads --history ~/Downloads/.smart-organizer/history.jsonl
smart-organizer ~/Downloads --undo --run-id <run-id>
smart-organizer --version
```

Launch interfaces directly:

```bash
smart-organizer-gui
smart-organizer-watch ~/Downloads
streamlit run streamlit_app.py
```

Wrapper scripts still work when you need to run without console commands:

```bash
python scripts/main.py ~/Downloads --dry-run
python scripts/gui.py
```

## Configuration

`config.example.json` is the committed template. For local customization:

```bash
cp config.example.json config.json      # Windows: copy config.example.json config.json
```

`config.json` is ignored by git because it can contain private API keys and
personal category data. The app falls back to `config.example.json` when no
local config exists.

Config loading is centralized and validated. Malformed JSON, empty category
lists, missing training data, and invalid extension settings fail fast with a
clear error instead of being silently ignored.

Smart Rename can read the NVIDIA key from either:

- `NVIDIA_API_KEY`
- `smart_rename.api_key` in local `config.json`

## AI Smart Rename

Smart Rename uses the NVIDIA OpenAI-compatible API to generate cleaner filenames
from extracted document text.

**Privacy:** with Smart Rename on, the first ~600 characters of each document are
sent to the NVIDIA API. Nothing is sent otherwise, and `--dry-run` never calls the
API. Renames happen as part of the move (one history entry, never overwriting an
existing file), so `--undo` restores the original name.

Setup:

0. `python -m pip install -e ".[rename]"`
1. Get an API key from `https://build.nvidia.com/models`.
2. Copy `config.example.json` to `config.json`.
3. Add your key under `smart_rename.api_key`, or set `NVIDIA_API_KEY`.
4. Run with `--smart-rename`.

## How Classification Works

Both back ends use one policy: a prediction is **low confidence** when the top score is
below a threshold or only narrowly beats the runner-up category. Low-confidence files go
to `Other` and are flagged for review.

- **Transformer** (`ai` extra): every example in `training_data`, plus your saved
  corrections, is embedded once. A document gets the category of its closest example,
  so custom categories work as soon as they have a few samples, and a correction takes
  effect immediately.
- **TF-IDF + Naive Bayes** (default, offline): retrained whenever you add a correction.

Tune `classifier.confidence_threshold`, `classifier.transformer_confidence_threshold`
and `classifier.min_margin` in `config.json`.

### Accuracy

`python scripts/evaluate_classifier.py` scores the classifier on 56 held-out labelled
documents in `tests/data/labeled_samples.json` (including short, noisy and ambiguous
ones). These are small, hand-written samples, so treat the numbers as a regression
guard rather than a benchmark on your own files.

| Model | Training data | Accuracy |
| --- | --- | --- |
| TF-IDF + Naive Bayes | v0.1.0 defaults (8 samples/category) | 80% (45/56) |
| TF-IDF + Naive Bayes | v0.2.0 defaults (16 samples/category) | 95% (53/56) |
| Transformer | v0.2.0 defaults | run `--transformer` (CI: *AI model tests*) |

Add your own corrections or training samples to improve results on your documents.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.10+ |
| ML Model | sentence-transformers (`all-MiniLM-L6-v2`) |
| Fallback Classifier | TF-IDF + Multinomial Naive Bayes |
| AI Smart Rename | NVIDIA NIM API (`meta/llama-3.1-8b-instruct`) |
| Language Detection | langdetect |
| Web App | Streamlit |
| Desktop GUI | Tkinter |
| File Extraction | pypdf, python-docx, openpyxl, python-pptx, extract-msg |
| Watch Mode | watchdog |

## Project Structure

```text
.
|-- smart_ai_file_organizer/ # Application package
|   |-- main.py              # CLI entry point
|   |-- gui.py               # Tkinter desktop GUI
|   |-- streamlit_app.py     # Streamlit web UI
|   |-- organizer.py         # File organization pipeline
|   |-- classifier.py        # Transformer/TF-IDF document classifier
|   |-- search.py            # Semantic search index and query engine
|   |-- duplicate_detector.py
|   |-- text_extractor.py
|   |-- renamer.py
|   |-- watcher.py
|   `-- undo.py
|-- streamlit_app.py         # Streamlit Cloud wrapper
|-- config.example.json      # Safe committed config template
|-- scripts/                 # Wrapper scripts + evaluate_classifier.py
|-- docs/                    # Roadmap, changelog, and media guidance
`-- tests/                   # Pytest suite
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest --cov=smart_ai_file_organizer --cov-report=term-missing
python -m build
```

The test suite sets `SMART_ORGANIZER_DISABLE_TRANSFORMERS=1` so CI and local
tests stay fast and offline-friendly. Install the `ai` extra and unset that
environment variable when you want to exercise the transformer path manually.

Coverage focuses on the core package logic. Tkinter, Streamlit, category-manager
widgets, and watch-mode event loops are excluded until their business logic is
extracted behind smaller testable adapters.

Release notes live in [`docs/CHANGELOG.md`](docs/CHANGELOG.md), the architecture
overview lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), release prep
lives in [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md), and planned
work lives in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Customizing Categories

Copy `config.example.json` to `config.json` and edit:

```json
{
  "categories": ["Finance", "Resume", "AI", "MyCategory"],
  "training_data": {
    "MyCategory": ["keywords describing this category..."]
  }
}
```

You can also use the Categories button in the desktop GUI.

## Security Notes

- Do not commit `config.json`, `.env`, logs, indexes, local documents, or API keys.
- Rotate any key that has ever been committed or shared.
- Review organized folders before running live moves on important data; use
  `--dry-run` first.
- Live runs write `.smart-organizer/history.jsonl` locally with source,
  destination, hash, action type, timestamp, and run id for reliable undo.
- `organizer.log` is for diagnostics only; undo uses structured history and
  refuses to restore a file whose content changed after the organize run.
- Smart Rename is the only feature that sends text off your machine (first ~600
  characters per file, only when enabled, never in dry-run).
- The search index is stored as JSON, never pickle, so a tampered cache cannot run code.
- Semantic search cache entries include file size, modified time, and content
  hash metadata so changed/deleted files are reindexed instead of served stale.

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Make a focused change and add tests where useful.
4. Run `python -m pytest`.
5. Push and open a pull request.

Full contribution guidance lives in [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
