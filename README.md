# 🗂️ Smart AI File Organizer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
  <img src="https://img.shields.io/github/last-commit/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=f59e0b"/>
  <img src="https://img.shields.io/github/repo-size/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=8b5cf6"/>
</p>

<p align="center">
  <b>Automatically classify, rename, and organise your files using Machine Learning — no manual sorting needed.</b>
</p>

---

## 📌 Overview

**Smart AI File Organizer** scans a folder, reads the content of each document, and uses a **sentence-transformers + Naive Bayes** machine learning pipeline to predict its category. Files are automatically moved into labelled sub-folders. An optional **AI Smart Rename** feature uses the NVIDIA free API to generate meaningful filenames from document content.

---

## ✨ Features

- 📄 Supports **PDF, DOCX, TXT, XLSX, PPTX, CSV, EML, MSG, ZIP, PNG, JPG**
- 🤖 **ML-based classification** — sentence-transformers + Naive Bayes (auto-selects best model)
- 🏷️ **AI Smart Rename** — renames files based on content using NVIDIA free API
- 🌐 **Language detection** — detects document language automatically
- 🗂️ **8 categories** — `Finance` · `Resume` · `AI` · `Research` · `Personal` · `Legal` · `Medical` · `Other`
- 🖥️ **Desktop GUI** — dark-themed Tkinter app with live activity log
- 👁️ **Watch Mode** — monitors folder in real-time, organises files as they arrive
- ↩️ **Undo** — restore all files to original locations with one click
- 📊 **Confidence scores** — shows how confident the model is for each file
- ✏️ **Manual override** — right-click any result to correct its category
- 🔍 **Dry Run (Preview)** — see what would happen before moving anything
- 📂 **Recursive scanning** — optionally organise files inside sub-folders
- 🔁 **Duplicate detection** via MD5 hashing — duplicates are skipped, never deleted
- 🛡️ **Collision-safe moves** — appends counter on name conflict
- ⚙️ **Config-driven** — customise categories in `config.example.json`, no code needed
- 🖼️ **Image OCR** via Tesseract (optional)
- 📝 **Full operation log** saved to `organizer.log`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| ML Model | sentence-transformers (`all-MiniLM-L6-v2`) |
| Fallback Classifier | TF-IDF + Multinomial Naive Bayes |
| AI Smart Rename | NVIDIA NIM API (free) — `meta/llama-3.1-8b-instruct` |
| Language Detection | langdetect |
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
├── classifier.py            # ML classifier (sentence-transformers / Naive Bayes)
├── renamer.py               # AI Smart Rename (NVIDIA API)
├── watcher.py               # Watch Mode (real-time monitoring)
├── undo.py                  # Undo last organise run
├── duplicate_detector.py    # MD5-based duplicate detection
├── text_extractor.py        # Text extraction for all file types
├── utils.py                 # Logging, folder creation, safe-move, scanner
├── config.example.json      # Example config (copy to config.json and add your key)
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
python main.py "D:\Downloads"                    # organise
python main.py "D:\Downloads" --dry-run          # preview
python main.py "D:\Downloads" --recursive        # include sub-folders
python main.py "D:\Downloads" --smart-rename     # AI Smart Rename
python main.py "D:\Downloads" --undo             # undo last run
python watcher.py "D:\Downloads"                 # watch mode
```

---

## 🏷️ AI Smart Rename Setup

Smart Rename uses the **NVIDIA free API** to generate meaningful filenames from document content.

**Example:**
```
scan0023.pdf         →  Invoice_Amazon_Mar2024_1299.pdf
doc_final_v3.docx    →  Resume_Software_Engineer_2024.docx
untitled_notes.txt   →  AI_Transformer_Research_Notes.txt
```

**Setup:**
1. Get your free API key at **https://build.nvidia.com/models**
2. Copy `config.example.json` → rename to `config.json`
3. Add your key:
```json
"smart_rename": {
    "enabled": false,
    "api_key": "nvapi-your-key-here"
}
```
4. In GUI — check **✏️ AI Smart Rename** before running

---

## 📂 Before & After

**Before:**
```
Downloads/
├── scan0023.pdf
├── doc_final_v3.docx
├── notes.txt
├── budget.xlsx
├── contract.pdf
└── report.eml
```

**After (with AI Smart Rename):**
```
Downloads/
├── Finance/   └── Invoice_Amazon_Mar2024_1299.pdf
├── Resume/    └── Resume_Software_Engineer_2024.docx
├── AI/        └── AI_Transformer_Research_Notes.txt
├── Finance/   └── Budget_Annual_2024.xlsx
├── Legal/     └── Legal_NDA_Contract_Acme.pdf
├── Personal/  └── Personal_Newsletter_March.eml
└── organizer.log
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```
Expected: **40 passed**

---

## ⚙️ Customising Categories

Copy `config.example.json` to `config.json` and edit:

```json
{
  "categories": ["Finance", "Resume", "AI", "MyNewCategory"],
  "training_data": {
    "MyNewCategory": ["keywords describing your category..."]
  }
}
```

---

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
