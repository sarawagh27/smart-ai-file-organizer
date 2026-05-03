"""Public Streamlit Cloud entrypoint for Smart AI File Organizer.

This file stays intentionally self-contained at import time so the hosted demo
renders immediately on Streamlit Cloud. Heavier project modules are imported
only inside button handlers.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Smart AI File Organizer",
    page_icon=":open_file_folder:",
    layout="wide",
    initial_sidebar_state="expanded",
)


CAT_COLORS = {
    "Finance": "#ef4444",
    "Resume": "#3b82f6",
    "AI": "#10b981",
    "Research": "#f97316",
    "Personal": "#8b5cf6",
    "Legal": "#ec4899",
    "Medical": "#06b6d4",
    "Other": "#64748b",
}

SUPPORTED = [
    "pdf",
    "txt",
    "docx",
    "xlsx",
    "pptx",
    "csv",
    "eml",
    "msg",
    "zip",
    "png",
    "jpg",
    "jpeg",
]

SAMPLE_FILES = [
    ("billing-invoice.xlsx", "Finance", "Invoice, payment, vendor, and billing terms."),
    ("resume_final_v3.pdf", "Resume", "Skills, work history, education, and project experience."),
    ("report_draft.docx", "Research", "Research notes, findings, methodology, and citations."),
    ("data.txt", "Personal", "Errands, appointments, reminders, and personal notes."),
]


def category_badge(category: str) -> str:
    color = CAT_COLORS.get(category, CAT_COLORS["Other"])
    return (
        f"<span style='background:{color}22;color:{color};border:1px solid {color}66;"
        "padding:0.2rem 0.55rem;border-radius:0.35rem;font-weight:700;'>"
        f"{category}</span>"
    )


def keyword_category(text: str) -> str:
    lowered = text.lower()
    rules = {
        "Finance": ["invoice", "payment", "bank", "tax", "receipt", "budget", "billing"],
        "Resume": ["resume", "cv", "skills", "experience", "education", "candidate"],
        "AI": ["machine learning", "neural", "model", "embedding", "ai", "llm"],
        "Research": ["abstract", "methodology", "study", "experiment", "research", "citation"],
        "Legal": ["contract", "agreement", "court", "legal", "clause"],
        "Medical": ["medical", "doctor", "patient", "diagnosis", "blood", "report"],
        "Personal": ["appointment", "errand", "personal", "family", "reminder"],
    }
    scores = {
        category: sum(1 for word in words if word in lowered)
        for category, words in rules.items()
    }
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score else "Other"


def classify_text(text: str) -> tuple[str, float, str]:
    """Classify text with the project classifier, falling back to keywords."""
    try:
        from smart_ai_file_organizer.classifier import DocumentClassifier

        classifier = DocumentClassifier()
        classifier.train()
        category, confidence, _is_low = classifier.predict_with_confidence(text)
        return category, confidence, "AI classifier"
    except Exception:
        return keyword_category(text), 65.0, "fast keyword fallback"


def extract_uploaded_text(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = Path(tmp.name)

    try:
        from smart_ai_file_organizer.text_extractor import extract_text

        return extract_text(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)


with st.sidebar:
    st.title("Smart AI File Organizer")
    page = st.radio(
        "View",
        ["Demo", "Classify Text", "Classify Files"],
        label_visibility="collapsed",
    )
    st.divider()
    st.link_button(
        "GitHub",
        "https://github.com/sarawagh27/smart-ai-file-organizer",
        use_container_width=True,
    )


st.title("Smart AI File Organizer")
st.caption("AI-powered file organization for messy local folders.")

if page == "Demo":
    st.subheader("How it organizes files")
    st.write(
        "Preview a folder, classify documents by content, then move them into "
        "category folders after you approve the dry run."
    )

    before, after = st.columns(2)
    with before:
        st.markdown("#### Messy folder")
        for filename, _category, preview in SAMPLE_FILES:
            st.code(f"{filename}\n{preview}", language="text")

    with after:
        st.markdown("#### Organized result")
        for filename, category, _preview in SAMPLE_FILES:
            st.markdown(
                f"{category_badge(category)} &nbsp; `{category}/{filename}`",
                unsafe_allow_html=True,
            )

    st.divider()
    st.image("docs/media/demo.gif", caption="Dry run, organize, and final folders")

elif page == "Classify Text":
    st.subheader("Try the classifier")
    text = st.text_area(
        "Paste document text",
        height=180,
        placeholder="Example: Invoice for monthly cloud hosting payment...",
    )
    if st.button("Classify text", type="primary", use_container_width=True):
        if len(text.strip()) < 20:
            st.warning("Paste at least 20 characters.")
        else:
            category, confidence, engine = classify_text(text)
            col1, col2, col3 = st.columns(3)
            col1.metric("Category", category)
            col2.metric("Confidence", f"{confidence:.1f}%")
            col3.metric("Engine", engine)
            st.progress(min(int(confidence), 100))

else:
    st.subheader("Classify uploaded files")
    uploads = st.file_uploader(
        "Upload files",
        type=SUPPORTED,
        accept_multiple_files=True,
    )
    if st.button("Classify files", type="primary", use_container_width=True):
        if not uploads:
            st.warning("Upload at least one file first.")
        else:
            for uploaded in uploads:
                with st.status(f"Reading {uploaded.name}", expanded=False):
                    try:
                        text = extract_uploaded_text(uploaded)
                        category, confidence, engine = classify_text(text)
                        st.markdown(
                            f"{category_badge(category)} `{uploaded.name}` "
                            f"- {confidence:.1f}% via {engine}",
                            unsafe_allow_html=True,
                        )
                    except Exception as exc:
                        st.error(f"{uploaded.name}: {exc}")
