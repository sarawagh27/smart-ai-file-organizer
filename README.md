# 🗂️ Smart AI File Organizer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/github/last-commit/your-username/smart-ai-file-organizer?style=for-the-badge&color=f59e0b" alt="Last Commit"/>
  <img src="https://img.shields.io/github/repo-size/your-username/smart-ai-file-organizer?style=for-the-badge&color=8b5cf6" alt="Repo Size"/>
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

- 📄 Supports **PDF**, **DOCX**, and **TXT** files
- 🤖 **ML-based classification** — TF-IDF vectoriser + Multinomial Naive Bayes
- 🗂️ Organises into **6 categories** — `Finance`, `Resume`, `AI`, `Research`, `Personal`, `Other`
- 🔁 **Duplicate detection** via MD5 hashing — duplicates are skipped, never deleted
- 📁 **Auto-creates** category folders if they don't exist
- 🛡️ **Collision-safe moves** — appends a counter on name conflict (e.g. `report_1.pdf`)
- 📝 **Full operation log** saved to `organizer.log` in the target folder
- 🖥️ Clean **CLI interface** with optional verbose/debug mode

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
| Duplicate Detection | MD5 hashing (`hashlib`) |
| Logging | Python `logging` (stdlib) |
| CLI | Python `argparse` (stdlib) |

---

## 📁 Project Structure

```
smart-ai-file-organizer/
├── main.py                  # CLI entry point
├── organizer.py             # Pipeline orchestrator
├── classifier.py            # TF-IDF + Naive Bayes classifier
├── duplicate_detector.py    # MD5-based duplicate detection
├── text_extractor.py        # Text extraction for PDF / DOCX / TXT
├── utils.py                 # Logging, folder creation, safe-move, scanner
├── requirements.txt         # Python dependencies
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
git clone https://github.com/your-username/smart-ai-file-organizer.git
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

---

## 🚀 Usage

```bash
# Organise a specific folder
python main.py "D:\Downloads"

# Organise the current directory
python main.py

# Enable verbose / debug output
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
├── user_manual.pdf
└── invoice_jan_copy.pdf   ← duplicate
```

**After** — automatically organised:

```
Downloads/
├── Finance/
│   └── invoice_jan.pdf
├── Resume/
│   └── my_resume.docx
├── AI/
│   └── transformer_notes.txt
├── Research/
│   └── research_paper.pdf
├── Personal/
│   └── diary_entry.txt
├── Other/
│   └── user_manual.pdf
├── invoice_jan_copy.pdf   ← duplicate skipped, left in place
└── organizer.log
```

---

## 🖥️ Example Terminal Output

```
🗂  Smart AI File Organizer
   Target : D:\Downloads
   Log    : D:\Downloads\organizer.log

2024-01-15 10:22:01 | INFO  | Training document classifier…
2024-01-15 10:22:01 | INFO  | Found 7 supported file(s) in 'D:\Downloads'.
2024-01-15 10:22:01 | INFO  | Processing: invoice_jan.pdf
2024-01-15 10:22:01 | INFO  |   ↳ Category: Finance
2024-01-15 10:22:01 | INFO  | Processing: my_resume.docx
2024-01-15 10:22:01 | INFO  |   ↳ Category: Resume
2024-01-15 10:22:01 | INFO  | Processing: transformer_notes.txt
2024-01-15 10:22:01 | INFO  |   ↳ Category: AI
2024-01-15 10:22:01 | WARNING | DUPLICATE — skipping 'invoice_jan_copy.pdf'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Smart AI File Organizer — Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total files found   : 7
  Successfully moved  : 6
  Duplicates skipped  : 1
  Errors              : 0
  ────────────────────────────────────────────
  Category              Files
  ────────────────────────────────────────────
  AI                        1
  Finance                   1
  Other                     1
  Personal                  1
  Research                  1
  Resume                    1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔮 Future Improvements

- [ ] **Recursive scanning** — organise files inside sub-folders too
- [ ] **Custom categories** — let users define their own labels via a config file
- [ ] **GUI interface** — drag-and-drop desktop app built with Tkinter or PyQt
- [ ] **Larger training corpus** — improve accuracy with a real labelled dataset
- [ ] **Image support** — classify `.png`, `.jpg` files using OCR (Tesseract)
- [ ] **Undo feature** — restore files to their original locations from the log
- [ ] **Watch mode** — monitor a folder in real-time and organise files as they arrive
- [ ] **Unit tests** — full test suite with `pytest`

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
