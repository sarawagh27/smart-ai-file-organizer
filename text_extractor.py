"""
text_extractor.py
-----------------
Handles text extraction from PDF, DOCX, and TXT files.
Each function returns the extracted text as a plain string.
"""

import logging

logger = logging.getLogger(__name__)


def extract_from_txt(filepath: str) -> str:
    """Read plain text from a .txt file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"TXT extraction failed for {filepath}: {e}")
        return ""


def extract_from_pdf(filepath: str) -> str:
    """Extract text from every page of a PDF using PyPDF2."""
    try:
        import PyPDF2

        text_parts = []
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF extraction failed for {filepath}: {e}")
        return ""


def extract_from_docx(filepath: str) -> str:
    """Extract text from all paragraphs in a .docx file using python-docx."""
    try:
        from docx import Document

        doc = Document(filepath)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed for {filepath}: {e}")
        return ""


def extract_text(filepath: str) -> str:
    """
    Dispatch to the correct extractor based on file extension.

    Returns:
        Extracted text string, or empty string on failure.
    """
    lower = filepath.lower()
    if lower.endswith(".txt"):
        return extract_from_txt(filepath)
    elif lower.endswith(".pdf"):
        return extract_from_pdf(filepath)
    elif lower.endswith(".docx"):
        return extract_from_docx(filepath)
    else:
        logger.warning(f"Unsupported file type: {filepath}")
        return ""
