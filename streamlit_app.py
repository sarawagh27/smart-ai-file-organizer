"""
streamlit_app.py
----------------
Web UI for Smart AI File Organizer — deployable on streamlit.io for free.

Features
--------
  - Upload any supported file
  - AI classifies it instantly (sentence-transformers or TF-IDF fallback)
  - Shows category, confidence bar, language detected
  - Shows content preview
  - Try with sample text
  - Fully deployable — no installation needed for users

Deploy
------
  1. Push this file to GitHub
  2. Go to https://streamlit.io/cloud
  3. Connect repo → select streamlit_app.py → Deploy

Run locally
-----------
  streamlit run streamlit_app.py
"""

import sys
import os
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart AI File Organizer",
    page_icon="🗂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 780px; }
    .stApp { background-color: #0f0f1a; color: #e2e8f0; }

    .category-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 8px 0;
    }
    .conf-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .preview-box {
        background: #1e1e2e;
        border: 1px solid #2a2a3e;
        border-radius: 10px;
        padding: 14px;
        font-size: 0.85rem;
        color: #94a3b8;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 180px;
        overflow-y: auto;
    }
    .meta-row {
        display: flex;
        gap: 16px;
        margin: 12px 0;
    }
    .meta-card {
        flex: 1;
        background: #1e1e2e;
        border: 1px solid #2a2a3e;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .meta-val { font-size: 1.2rem; font-weight: 700; color: #e2e8f0; }
    .meta-lbl { font-size: 0.75rem; color: #64748b; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Category config ───────────────────────────────────────────────────────────
CAT_COLORS = {
    "Finance":  "#ef4444",
    "Resume":   "#3b82f6",
    "AI":       "#10b981",
    "Research": "#f97316",
    "Personal": "#8b5cf6",
    "Legal":    "#ec4899",
    "Medical":  "#06b6d4",
    "Other":    "#64748b",
}
CAT_ICONS = {
    "Finance": "💰", "Resume": "📋", "AI": "🤖",
    "Research": "🔬", "Personal": "📖", "Legal": "⚖️",
    "Medical": "🏥", "Other": "📁",
}

SUPPORTED = [".pdf", ".txt", ".docx", ".xlsx", ".pptx",
             ".csv", ".eml", ".msg", ".zip", ".png", ".jpg", ".jpeg"]

# ── Load classifier (cached so it only loads once) ────────────────────────────
@st.cache_resource(show_spinner="Loading AI model…")
def load_classifier():
    from classifier import DocumentClassifier
    clf = DocumentClassifier()
    clf.train()
    return clf

@st.cache_resource(show_spinner=False)
def get_language_tools():
    from classifier import detect_language, LANGUAGE_NAMES
    return detect_language, LANGUAGE_NAMES

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🗂️ Smart AI File Organizer")
st.markdown("Upload any document — AI reads the content and classifies it instantly.")
st.divider()

# ── Tabs: Upload file | Try with text ────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 Upload File", "✏️ Try with Text"])

# ── Tab 1: File upload ────────────────────────────────────────────────────────
with tab1:
    uploaded = st.file_uploader(
        "Drop a file here",
        type=[s.lstrip(".") for s in SUPPORTED],
        help=f"Supported: {', '.join(SUPPORTED)}",
    )

    if uploaded:
        ext = Path(uploaded.name).suffix.lower()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        with st.spinner("Extracting text and classifying…"):
            try:
                from text_extractor import extract_text
                text = extract_text(tmp_path)
                os.unlink(tmp_path)

                clf = load_classifier()
                detect_language, LANGUAGE_NAMES = get_language_tools()

                category, confidence, is_low = clf.predict_with_confidence(text)
                lang_code = detect_language(text)
                lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())

                # ── Result ────────────────────────────────────────────────────
                st.success("Classification complete!")

                color = CAT_COLORS.get(category, "#64748b")
                icon  = CAT_ICONS.get(category, "📁")

                st.markdown(f"""
                <div style="text-align:center; padding: 20px 0;">
                    <div style="font-size:3rem;">{icon}</div>
                    <div class="category-badge" style="background:{color}22; color:{color}; border: 2px solid {color};">
                        {category}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Confidence bar
                conf_color = "#fbbf24" if is_low else "#4ade80"
                st.markdown(f'<p class="conf-label">Confidence</p>', unsafe_allow_html=True)
                st.progress(int(confidence), text=f"{confidence:.1f}%")
                if is_low:
                    st.warning("⚠️ Low confidence — the model is uncertain about this file.")

                # Meta cards
                st.markdown(f"""
                <div class="meta-row">
                    <div class="meta-card">
                        <div class="meta-val">{confidence:.1f}%</div>
                        <div class="meta-lbl">Confidence</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-val">{lang_name}</div>
                        <div class="meta-lbl">Language</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-val">{len(text.split()):,}</div>
                        <div class="meta-lbl">Words extracted</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Content preview
                if text.strip():
                    preview = " ".join(text.split())[:400]
                    if len(text.strip()) > 400:
                        preview += "…"
                    st.markdown("**📄 Content Preview**")
                    st.markdown(f'<div class="preview-box">{preview}</div>',
                                unsafe_allow_html=True)

            except Exception as exc:
                st.error(f"Error processing file: {exc}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

# ── Tab 2: Try with text ──────────────────────────────────────────────────────
with tab2:
    st.markdown("Paste any text and see how the AI classifies it.")

    sample_texts = {
        "— pick a sample —": "",
        "Finance document": "Invoice #1234 — Payment due: Amazon Web Services — Amount: $2,500.00 — Tax: $225 — Total: $2,725. Please process payment within 30 days. Bank transfer to account ending 4521.",
        "AI/ML paper": "We propose a novel transformer architecture for natural language processing. Our model uses multi-head self-attention with 12 layers and 768 hidden dimensions, trained on a dataset of 100 billion tokens using the AdamW optimizer.",
        "Medical report": "Patient presents with elevated blood pressure (145/92 mmHg) and fasting glucose of 118 mg/dL. CBC shows hemoglobin 11.2 g/dL. Recommend follow-up in 4 weeks and dietary modifications.",
        "Legal contract": "This Non-Disclosure Agreement is entered into between the parties. The receiving party agrees to hold confidential information in strict confidence and not to disclose it to any third party without prior written consent.",
    }

    choice = st.selectbox("Load a sample:", list(sample_texts.keys()))
    text_input = st.text_area(
        "Or type your own text:",
        value=sample_texts[choice],
        height=160,
        placeholder="Paste document text here…",
    )

    if st.button("🔍 Classify Text", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text first.")
        elif len(text_input.strip()) < 20:
            st.warning("Please enter at least 20 characters.")
        else:
            with st.spinner("Classifying…"):
                clf = load_classifier()
                detect_language, LANGUAGE_NAMES = get_language_tools()

                category, confidence, is_low = clf.predict_with_confidence(text_input)
                lang_code = detect_language(text_input)
                lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())

                color = CAT_COLORS.get(category, "#64748b")
                icon  = CAT_ICONS.get(category, "📁")

                st.markdown(f"""
                <div style="text-align:center; padding: 16px 0;">
                    <div style="font-size:2.5rem;">{icon}</div>
                    <div class="category-badge" style="background:{color}22; color:{color}; border: 2px solid {color};">
                        {category}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.progress(int(confidence), text=f"Confidence: {confidence:.1f}%")

                if is_low:
                    st.warning("⚠️ Low confidence — try adding more descriptive text.")

                col1, col2 = st.columns(2)
                col1.metric("Category", f"{icon} {category}")
                col2.metric("Language", lang_name)

# ── Sidebar: About ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ About")
    st.markdown("""
    **Smart AI File Organizer** uses machine learning to automatically classify documents.

    **Supported file types:**
    PDF · DOCX · TXT · XLSX · PPTX · CSV · EML · MSG · ZIP · PNG · JPG

    **Categories:**
    💰 Finance · 📋 Resume · 🤖 AI · 🔬 Research · 📖 Personal · ⚖️ Legal · 🏥 Medical · 📁 Other

    **Powered by:**
    - sentence-transformers (`all-MiniLM-L6-v2`)
    - scikit-learn (TF-IDF fallback)
    - langdetect
    """)

    st.divider()
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-View%20Source-black?logo=github)](https://github.com/sarawagh27/smart-ai-file-organizer)")

