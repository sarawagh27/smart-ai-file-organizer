# 🗂️ Smart AI File Organizer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
  <img src="https://img.shields.io/github/last-commit/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=f59e0b"/>
  <img src="https://img.shields.io/github/repo-size/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=8b5cf6"/>
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

- 📄 Supports **PDF, DOCX, TXT, XLSX, PPTX, CSV, EML, MSG, ZIP, PNG, JPG**
- 🤖 **ML-based classification** — TF-IDF vectoriser + Multinomial Naive Bayes
- 🗂️ **8 categories** — `Finance` · `Resume` · `AI` · `Research` · `Personal` · `Legal` · `Medical` · `Other`
- 🖥️ **Desktop GUI** — dark-themed Tkinter app with live activity log
- 👁️ **Watch Mode** — monitors folder in real-time, organises files as they arrive
- ↩️ **Undo** — restore all files to their original locations with one click
- 📊 **Progress bar** — visual progress when processing large folders (CLI)
- 🔍 **Dry Run (Preview)** — see what would happen before moving anything
- 📂 **Recursive scanning** — optionally organise files inside sub-folders
- 🔁 **Duplicate detection** via MD5 hashing — duplicates are skipped, never deleted
- 🛡️ **Collision-safe moves** — appends counter on name conflict (e.g. `report_1.pdf`)
- ⚙️ **Config-driven** — customise categories in `config.json`, no code needed
- 🖼️ **Image OCR** via Tesseract (optional)
- 📝 **Full operation log** saved to 
- 📊 **Statistics dashboard** — pie chart and run history built into the GUI`organizer.log`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| ML Pipeline | scikit-learn |
| Vectorisation | TF-IDF (`TfidfVectorizer`) |
| Classifier | Multinomial Naive Bayes |
| PDF | PyPDF2 |
| DOCX | python-docx |
| XLSX | openpyxl |
| PPTX | python-pptx |
| EML | Python `email` (stdlib) |
| MSG | extract-msg |
| ZIP | Python `zipfile` (stdlib) |
| Image OCR | pytesseract + Pillow (optional) |
| Watch Mode | watchdog |
| Progress Bar | tqdm |
| GUI | Tkinter (built-in) |
| Duplicate Detection | MD5 hashing (`hashlib`) |

---

## 📁 Project Structure

```
smart-ai-file-organizer/
├── main.py                  # CLI entry point
├── gui.py                   # Desktop GUI (Tkinter)
├── organizer.py             # Pipeline orchestrator
├── watcher.py               # Watch Mode (real-time monitoring)
├── undo.py                  # Undo last organise run
├── classifier.py            # TF-IDF + Naive Bayes classifier
├── duplicate_detector.py    # MD5-based duplicate detection
├── text_extractor.py        # Text extraction for all file types
├── utils.py                 # Logging, folder creation, safe-move, scanner
├── config.json              # Categories, training data, settings
├── requirements.txt
├── tests/
│   ├── test_classifier.py
│   ├── test_duplicate_detector.py
│   ├── test_organizer.py
│   └── test_text_extractor.py
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/sarawagh27/smart-ai-file-organizer.git
cd smart-ai-file-organizer
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

---

## 🚀 Usage

### GUI (recommended)
```bash
python gui.py
```

### CLI
```bash
python main.py "D:\Downloads"                   # organise
python main.py "D:\Downloads" --dry-run         # preview
python main.py "D:\Downloads" --recursive       # include sub-folders
python main.py "D:\Downloads" --undo            # undo last run
python main.py "D:\Downloads" --undo --dry-run  # preview undo
python watcher.py "D:\Downloads"                # watch mode
```

---

## 📂 Before & After

**Before:**
```
Downloads/
├── invoice_jan.pdf
├── my_resume.docx
├── ai_notes.txt
├── budget.xlsx
├── legal_contract.pdf
├── medical_report.pdf
├── newsletter.eml
└── archive.zip
```

**After:**
```
Downloads/
├── Finance/   └── invoice_jan.pdf, budget.xlsx
├── Resume/    └── my_resume.docx
├── AI/        └── ai_notes.txt
├── Legal/     └── legal_contract.pdf
├── Medical/   └── medical_report.pdf
├── Personal/  └── newsletter.eml
├── Other/     └── archive.zip
└── organizer.log
```

---

## 🖥️ Example CLI Output (with progress bar)

```
🗂  Smart AI File Organizer
   Target    : D:\Downloads
   Mode      : LIVE

Organising: [████████████] 100% | 8/8 files [00:03]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Smart AI File Organizer — Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total files found   : 8
  Successfully moved  : 8
  Duplicates skipped  : 0
  Errors              : 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ⚙️ Customising Categories

Edit `config.json` — no code changes needed:

```json
{
  "categories": ["Finance", "Resume", "AI", "MyNewCategory"],
  "training_data": {
    "MyNewCategory": ["keywords describing your category..."]
  }
}
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```
Expected: **40 passed**

---

## 🔮 Future Improvements

- [x] ~~GUI interface~~ ✅
- [x] ~~Recursive scanning~~ ✅
- [x] ~~Custom categories via config~~ ✅
- [x] ~~Image support (OCR)~~ ✅
- [x] ~~Unit tests~~ ✅
- [x] ~~Larger training corpus~~ ✅
- [x] ~~Watch mode~~ ✅
- [x] ~~Undo feature~~ ✅
- [x] ~~Progress bar~~ ✅
- [x] ~~More file types (EML, MSG, ZIP)~~ ✅

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add: description"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

MIT — free to use and modify.

---

<p align="center">Made with ❤️ and Python</p>
