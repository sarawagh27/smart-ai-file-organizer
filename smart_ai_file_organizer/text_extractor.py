"""
text_extractor.py
-----------------
Extracts text from all supported file types:
  - TXT / CSV  : plain read
  - PDF        : pypdf (with OCR fallback for scanned PDFs)
  - DOCX       : python-docx
  - XLSX       : openpyxl
  - PPTX       : python-pptx
  - EML        : Python stdlib email module
  - MSG        : extract-msg library
  - ZIP        : extracts and reads text files inside the archive
  - Images     : pytesseract OCR (optional)
"""

import io
import logging
import os
import shutil

logger = logging.getLogger(__name__)

# Safety caps so one huge file cannot stall a run or exhaust memory.
MAX_CHARS = 2_000_000
MAX_PDF_PAGES = 50
MAX_OCR_PAGES = 5
MIN_USEFUL_TEXT = 20     # a PDF page layer shorter than this is treated as "scanned"


# ── Tesseract (optional OCR) ─────────────────────────────────────────────────
def _find_tesseract() -> str | None:
    """Locate the tesseract binary: PATH first, then common install folders."""
    found = shutil.which("tesseract")
    if found:
        return found
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Tesseract-OCR", "tesseract.exe"),
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    return next((c for c in candidates if os.path.exists(c)), None)


def _configure_tesseract() -> bool:
    """Point pytesseract at the binary. Returns False if OCR is unavailable."""
    try:
        import pytesseract
    except ImportError:
        return False
    binary = _find_tesseract()
    if binary is None:
        return False
    pytesseract.pytesseract.tesseract_cmd = binary
    return True


SUPPORTED_EXTENSIONS = {
    ".txt", ".csv", ".pdf", ".docx",
    ".xlsx", ".pptx",
    ".eml", ".msg", ".zip",
    ".png", ".jpg", ".jpeg",
}


def extract_from_txt(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(MAX_CHARS)
    except Exception as e:
        logger.error("TXT extraction failed for %s: %s", filepath, e)
        return ""


def _ocr_pdf_images(reader) -> str:
    """OCR the embedded page images of a scanned PDF (first few pages only)."""
    if not _configure_tesseract():
        logger.info("Scanned PDF but OCR unavailable (install pytesseract + Tesseract).")
        return ""
    import pytesseract
    from PIL import Image

    parts = []
    for page in reader.pages[:MAX_OCR_PAGES]:
        try:
            for image in page.images:
                parts.append(pytesseract.image_to_string(Image.open(io.BytesIO(image.data))))
        except Exception as e:
            logger.debug("OCR skipped one PDF page image: %s", e)
    return "\n".join(p for p in parts if p.strip())


def extract_from_pdf(filepath: str) -> str:
    try:
        try:
            from pypdf import PdfReader
        except ImportError:                      # older installs
            from PyPDF2 import PdfReader
        parts = []
        with open(filepath, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages[:MAX_PDF_PAGES]:
                text = page.extract_text()
                if text:
                    parts.append(text)
            text = "\n".join(parts)
            if len(text.strip()) < MIN_USEFUL_TEXT:      # likely a scan → OCR fallback
                text = _ocr_pdf_images(reader) or text
        return text[:MAX_CHARS]
    except Exception as e:
        logger.error("PDF extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error("DOCX extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_xlsx(filepath: str) -> str:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
        parts = []
        total = 0
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        value = str(cell)
                        parts.append(value)
                        total += len(value) + 1
                if total >= MAX_CHARS:
                    break
            if total >= MAX_CHARS:
                break
        wb.close()
        return " ".join(parts)[:MAX_CHARS]
    except Exception as e:
        logger.error("XLSX extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_pptx(filepath: str) -> str:
    try:
        from pptx import Presentation
        prs = Presentation(filepath)
        parts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            parts.append(text)
        return "\n".join(parts)
    except Exception as e:
        logger.error("PPTX extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_eml(filepath: str) -> str:
    """Extract subject + body from a .eml email file using stdlib."""
    try:
        import email
        from email import policy
        with open(filepath, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        parts = []
        # Subject and sender give good classification signals
        if msg.get("subject"):
            parts.append(msg["subject"])
        if msg.get("from"):
            parts.append(msg["from"])

        # Extract plain-text body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        parts.append(payload.decode("utf-8", errors="ignore"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                parts.append(payload.decode("utf-8", errors="ignore"))

        return "\n".join(parts)
    except Exception as e:
        logger.error("EML extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_msg(filepath: str) -> str:
    """Extract subject + body from an Outlook .msg file using extract-msg."""
    try:
        import extract_msg
        with extract_msg.openMsg(filepath) as msg:
            parts = []
            if msg.subject:
                parts.append(msg.subject)
            if msg.sender:
                parts.append(msg.sender)
            if msg.body:
                parts.append(msg.body)
            return "\n".join(str(p) for p in parts if p)
    except ImportError:
        logger.warning(
            "extract-msg not installed — skipping MSG for %s. "
            "Install with: pip install extract-msg", filepath
        )
        return ""
    except Exception as e:
        logger.error("MSG extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_zip(filepath: str) -> str:
    """
    Open a ZIP archive and extract text from any supported text files inside.
    Reads up to 10 text files to keep processing fast.
    """
    try:
        import zipfile
        parts = []
        text_exts = {".txt", ".csv", ".md", ".py", ".js", ".html", ".xml", ".json"}
        count = 0

        with zipfile.ZipFile(filepath, "r") as zf:
            for name in zf.namelist():
                if count >= 10:
                    break
                ext = "." + name.lower().rsplit(".", 1)[-1] if "." in name else ""
                if ext in text_exts:
                    try:
                        with zf.open(name) as inner:
                            # Bounded read: a "zip bomb" member never gets fully inflated.
                            content = inner.read(8000).decode("utf-8", errors="ignore")
                            parts.append(content[:2000])  # cap per file
                            count += 1
                    except Exception:
                        continue

        return "\n".join(parts)
    except Exception as e:
        logger.error("ZIP extraction failed for %s: %s", filepath, e)
        return ""


def extract_from_image(filepath: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        if not _configure_tesseract():
            logger.warning("Tesseract binary not found — skipping OCR for %s.", filepath)
            return ""
        with Image.open(filepath) as img:
            return pytesseract.image_to_string(img)
    except ImportError:
        logger.warning(
            "pytesseract / Pillow not installed — skipping OCR for %s.", filepath
        )
        return ""
    except Exception as e:
        logger.error("Image OCR failed for %s: %s", filepath, e)
        return ""


def extract_text(filepath: str) -> str:
    """Route to the correct extractor based on file extension."""
    ext = "." + filepath.lower().rsplit(".", 1)[-1] if "." in filepath else ""

    dispatch = {
        ".txt":  extract_from_txt,
        ".csv":  extract_from_txt,
        ".pdf":  extract_from_pdf,
        ".docx": extract_from_docx,
        ".xlsx": extract_from_xlsx,
        ".pptx": extract_from_pptx,
        ".eml":  extract_from_eml,
        ".msg":  extract_from_msg,
        ".zip":  extract_from_zip,
        ".png":  extract_from_image,
        ".jpg":  extract_from_image,
        ".jpeg": extract_from_image,
    }

    handler = dispatch.get(ext)
    if handler is None:
        logger.warning("Unsupported file type: %s", filepath)
        return ""
    return handler(filepath)
