# 🗂️ Smart AI File Organizer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
  <img src="https://img.shields.io/github/last-commit/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=f59e0b"/>
  <img src="https://img.shields.io/github/repo-size/sarawagh27/smart-ai-file-organizer?style=for-the-badge&color=8b5cf6"/>
  <a href="https://smart-ai-file-organizer.streamlit.app">
    <img src="https://img.shields.io/badge/Live%20Demo-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white"/>
  </a>
</p>

<p align="center">
  <b>Automatically classify, rename, and organise your files using Machine Learning — no manual sorting needed.</b>
</p>

<p align="center">
  <a href="https://smart-ai-file-organizer.streamlit.app">🌐 Try it live → smart-ai-file-organizer.streamlit.app</a>
</p>

---

## 📌 Overview

**Smart AI File Organizer** scans a folder, reads the content of each document, and uses a **sentence-transformers** machine learning model to predict its category. Files are automatically moved into labelled sub-folders. An optional **AI Smart Rename** feature uses the NVIDIA free API to generate meaningful filenames from document content.

Available as both a **desktop GUI app** and a **live web app**.

---

## ✨ Features

### 🖥️ Desktop App
- 📄 Supports **PDF, DOCX, TXT, XLSX, PPTX, CSV, EML, MSG, ZIP, PNG, JPG**
- 🤖 **ML classification** — sentence-transformers + Naive Bayes fallback
- 🏷️ **AI Smart Rename** — renames files based on content (NVIDIA free API)
- 🌐 **Language detection** — detects document language automatically
- 🗂️ **8 categories** — Finance · Resume · AI · Research · Personal · Legal · Medical · Other
- 👁️ **Watch Mode** — monitors folder in real-time
- ↩️ **Undo** — restore files to original locations
- 📊 **Confidence scores** — know how certain the model is
- ✏️ **Manual override** — right-click to correct any category
- 🔍 **Dry Run** — preview before moving anything
- 📂 **Recursive scanning** — include sub-folders
- 🔁 **Duplicate detection** via MD5 hashing
- ⚙️ **Category Manager** — add/edit/delete categories from GUI
- ⌨️ **Keyboard shortcuts** — Ctrl+R, Ctrl+W, Ctrl+Z, Ctrl+K
- 📥 **Export to styled Excel** — colour-coded results spreadsheet
- 📝 **Full operation log** saved to `organizer.log`

### 🌐 Web App (live demo)
- Upload any supported file → instant AI classification
- Confidence scores + language detection
- Manual category override (model learns from corrections)
- AI Smart Rename (bring your own NVIDIA key)
- Export results as CSV or styled Excel
- Category Manager — add/edit/delete categories
- Try with sample text

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| ML Model | sentence-transformers (`all-MiniLM-L6-v2`) |
| Fallback Classifier | TF-IDF + Multinomial Naive Bayes |
| AI Smart Rename | NVIDIA NIM API (free) — `meta/llama-3.1-8b-instruct` |
| Language Detection | langdetect |
| Web App | Streamlit |
| Desktop GUI | Tkinter |
| PDF | PyPDF2 |
| DOCX | python-docx |
| XLSX | openpyxl |
| PPTX | python-pptx |
| Watch Mode | watchdog |
| Duplicate Detection | MD5 hashing |

---

## 📁 Project Structure

```
smart-ai-file-organizer/
├── main.py                  # CLI entry point
├── gui.py                   # Desktop GUI (Tkinter)
├── streamlit_app.py         # Web app (Streamlit)
├── organizer.py             # Pipeline orchestrator
├── classifier.py            # ML classifier
├── renamer.py               # AI Smart Rename (NVIDIA API)
├── category_manager.py      # Category Manager GUI popup
├── watcher.py               # Watch Mode
├── undo.py                  # Undo last run
├── duplicate_detector.py    # MD5 duplicate detection
├── text_extractor.py        # Text extraction for all file types
├── utils.py                 # Shared helpers
├── config.example.json      # Config template
├── requirements.txt         # Desktop dependencies
├── requirements_streamlit.txt # Web app dependencies
└── tests/                   # 40 unit tests
```

---

## ⚙️ Installation (Desktop)

```bash
git clone https://github.com/sarawagh27/smart-ai-file-organizer.git
cd smart-ai-file-organizer
pip install -r requirements.txt
```

---

## 🚀 Usage

### Web App (no installation)
👉 **[smart-ai-file-organizer.streamlit.app](https://smart-ai-file-organizer.streamlit.app)**

### Desktop GUI
```bash
python gui.py
```

### CLI
```bash
python main.py "D:\Downloads"                    # organise
python main.py "D:\Downloads" --dry-run          # preview
python main.py "D:\Downloads" --recursive        # sub-folders
python main.py "D:\Downloads" --smart-rename     # AI rename
python main.py "D:\Downloads" --undo             # undo last run
```

---

## 🏷️ AI Smart Rename

Renames files based on their content using the **NVIDIA free API**.

```
scan0023.pdf         →  Invoice_Amazon_Mar2024_1299.pdf
doc_final_v3.docx    →  Resume_Software_Engineer_2024.docx
untitled_notes.txt   →  AI_Transformer_Research_Notes.txt
```

**Setup:**
1. Get free key at **https://build.nvidia.com/models**
2. Copy `config.example.json` → `config.json`
3. Add your key to `config.json` under `smart_rename.api_key`

---

## 📂 Before & After

**Before:**
```
Downloads/
├── scan0023.pdf
├── doc_final_v3.docx
├── notes.txt
├── budget.xlsx
└── contract.pdf
```

**After:**
```
Downloads/
├── Finance/   └── Invoice_Amazon_Mar2024_1299.pdf
├── Resume/    └── Resume_Software_Engineer_2024.docx
├── AI/        └── AI_Transformer_Research_Notes.txt
├── Finance/   └── Budget_Annual_2024.xlsx
└── Legal/     └── Legal_NDA_Contract_Acme.pdf
```

---

## 🧪 Tests

```bash
python -m pytest tests/ -v
```
Expected: **40 passed**

---

## ⚙️ Customising Categories

Copy `config.example.json` to `config.json` and edit:

```json
{
  "categories": ["Finance", "Resume", "AI", "MyCategory"],
  "training_data": {
    "MyCategory": ["keywords describing this category..."]
  }
}
```

Or use the **⚙️ Categories** button in the desktop GUI.

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add: description"`
4. Push and open a Pull Request

---

## 📄 License

MIT — free to use and modify.

---

<p align="center">Made with ❤️ and Python</p>
