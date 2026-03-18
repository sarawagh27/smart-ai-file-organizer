# 🗂️ Smart AI File Organizer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/github/last-commit/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=f59e0b" alt="Last Commit"/>
  <img src="https://img.shields.io/github/repo-size/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=8b5cf6" alt="Repo Size"/>
</p>

<p align="center">
  <b>Automatically classify and organise your files using Machine Learning — no manual sorting needed.</b>
</p>

---

## 📌 Overview

**Smart AI File Organizer** scans a folder, reads the content of each document, and uses a **TF-IDF + Naive Bayes** machine learning pipeline to predict its category. Files are then automatically moved into labelled sub-folders. Duplicate files are detected via **MD5 hashing** and safely skipped.

No cloud. No API keys. Runs entirely on your machine.

---

## ✨ Features

- 📄 Supports **PDF, DOCX, TXT, XLSX, PPTX, CSV, PNG, JPG** files
- 🤖 **ML-based classification** — TF-IDF vectoriser + Multinomial Naive Bayes
- 🗂️ Organises into **8 categories** — `Finance` · `Resume` · `AI` · `Research` · `Personal` · `Legal` · `Medical` · `Other`
- 🖥️ **Desktop GUI** — dark-themed Tkinter app with live activity log
- 📂 **Recursive scanning** — optionally organise files inside sub-folders too
- 🔍 **Dry Run (Preview) mode** — see what would happen before moving anything
- 🔁 **Duplicate detection** via MD5 hashing — duplicates are skipped, never deleted
- 📁 **Auto-creates** category folders if they don't exist
- 🛡️ **Collision-safe moves** — appends a counter on name conflict (e.g. `report_1.pdf`)
- 🖼️ **OCR support** for images via Tesseract (optional)
- ⚙️ **Config-driven** — customise categories and training data in `config.json`, no code changes needed
- 📝 **Full operation log** saved to `organizer.log` in the target folder

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| ML Pipeline | scikit-learn |
| Vectorisation | TF-IDF (`TfidfVectorizer`) |
| Classifier | Multinomial Naive Bayes |
| PDF Extraction | PyPDF2 |
| DOCX Extraction | python-docx |
| XLSX Extraction | openpyxl |
| PPTX Extraction | python-pptx |
| Image OCR | pytesseract + Pillow (optional) |
| Duplicate Detection | MD5 hashing (`hashlib`) |
| GUI | Tkinter (built-in) |
| Logging | Python `logging` (stdlib) |
| CLI | Python `argparse` (stdlib) |

---

## 📁 Project Structure

```
smart-ai-file-organizer/
├── main.py                  # CLI entry point
├── gui.py                   # Desktop GUI (Tkinter)
├── organizer.py             # Pipeline orchestrator
├── classifier.py            # TF-IDF + Naive Bayes classifier
├── duplicate_detector.py    # MD5-based duplicate detection
├── text_extractor.py        # Text extraction for all file types
├── utils.py                 # Logging, folder creation, safe-move, scanner
├── config.json              # Categories, training data, settings
├── requirements.txt         # Python dependencies
├── tests/                   # Unit tests (pytest)
│   ├── test_classifier.py
│   ├── test_duplicate_detector.py
│   ├── test_organizer.py
│   └── test_text_extractor.py
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### Prerequisites
- Python **3.10** or higher
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/sarawagh27/smart-ai-file-organizer.git
cd smart-ai-file-organizer

# 2. Create a virtual environment
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Optional: Image OCR support
To classify image files (PNG, JPG), install Tesseract:

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and note the path (default: `C:\Program Files\Tesseract-OCR\`)
3. Then run:
```bash
pip install pytesseract
```

---

## 🚀 Usage

### GUI (recommended)
```bash
python gui.py
```
Opens a dark-themed desktop app — browse a folder, preview changes, then organise.

### CLI
```bash
# Organise a specific folder
python main.py "D:\Downloads"

# Preview only — no files moved
python main.py "D:\Downloads" --dry-run

# Include sub-folders (recursive)
python main.py "D:\Downloads" --recursive

# Verbose / debug output
python main.py "D:\Downloads" -v

# Show help
python main.py --help
```

---

## 📂 Before & After

**Before** — messy, unsorted folder:

```
Downloads/
├── invoice_jan.pdf
├── my_resume.docx
├── transformer_notes.txt
├── research_paper.pdf
├── diary_entry.txt
├── budget_2024.xlsx
├── presentation.pptx
└── invoice_jan_copy.pdf   ← duplicate
```

**After** — automatically organised:

```
Downloads/
├── Finance/
│   └── invoice_jan.pdf
│   └── budget_2024.xlsx
├── Resume/
│   └── my_resume.docx
├── AI/
│   └── transformer_notes.txt
├── Research/
│   └── research_paper.pdf
├── Personal/
│   └── diary_entry.txt
├── Other/
│   └── presentation.pptx
├── invoice_jan_copy.pdf   ← duplicate skipped, left in place
└── organizer.log
```

---

## 🖥️ Example Terminal Output

```
🗂  Smart AI File Organizer
   Target    : D:\Downloads
   Mode      : LIVE
   Recursive : False
   Log       : D:\Downloads\organizer.log

2026-03-18 10:22:01 | INFO  | Classifier trained — 62 samples across 8 categories.
2026-03-18 10:22:01 | INFO  | Found 7 supported file(s) in 'D:\Downloads'.
2026-03-18 10:22:01 | INFO  | Processing: invoice_jan.pdf
2026-03-18 10:22:01 | INFO  |   ↳ Category: Finance
2026-03-18 10:22:01 | INFO  | Processing: my_resume.docx
2026-03-18 10:22:01 | INFO  |   ↳ Category: Resume
2026-03-18 10:22:01 | WARNING | DUPLICATE — skipping 'invoice_jan_copy.pdf'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Smart AI File Organizer — Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total files found   : 7
  Successfully moved  : 6
  Duplicates skipped  : 1
  Errors              : 0
  ──────────────────────────────────────────────
  Category               Files
  ──────────────────────────────────────────────
  AI                         1
  Finance                    2
  Other                      1
  Personal                   1
  Research                   1
  Resume                     1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ⚙️ Customising Categories

Edit `config.json` to add, rename, or remove categories — no code changes needed:

```json
{
  "categories": ["Finance", "Resume", "AI", "Research", "Personal", "Legal", "Medical", "Other"],
  "training_data": {
    "Finance": ["invoice payment bank balance tax revenue..."],
    "MyNewCategory": ["your custom keywords here..."]
  }
}
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

Expected output: **40 passed**

---

## 🔮 Future Improvements

- [x] ~~GUI interface~~ ✅ Done
- [x] ~~Recursive scanning~~ ✅ Done
- [x] ~~Custom categories via config file~~ ✅ Done
- [x] ~~Image support (OCR)~~ ✅ Done
- [x] ~~Unit tests~~ ✅ Done
- [x] ~~Larger training corpus~~ ✅ Done (62 samples, 8 categories)
- [ ] **Watch mode** — monitor a folder in real-time and organise as files arrive
- [ ] **Undo feature** — restore files to original locations from the log
- [ ] **Progress bar** — visual progress for large folders
- [ ] **More file types** — support for `.eml`, `.msg`, `.zip`

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit** your changes
   ```bash
   git commit -m "Add: your feature description"
   ```
4. **Push** to your branch
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** and describe what you've changed

Please keep code clean, commented, and consistent with the existing modular structure.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Made with ❤️ and Python</p>
