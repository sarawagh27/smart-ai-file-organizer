"""Compatibility wrapper for Streamlit Cloud and `streamlit run streamlit_app.py`."""

try:
    from smart_ai_file_organizer.streamlit_app import *  # noqa: F403
except Exception as exc:
    import streamlit as st

    try:
        st.set_page_config(
            page_title="Smart AI File Organizer",
            page_icon=":open_file_folder:",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass

    st.error("Smart AI File Organizer failed to start.")
    st.exception(exc)
    raise
