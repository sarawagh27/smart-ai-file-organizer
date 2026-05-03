"""Compatibility wrapper for Streamlit Cloud and `streamlit run streamlit_app.py`.

Streamlit Cloud executes this root file. Run the package app file as the main
script instead of importing it so Streamlit reliably attaches UI deltas to the
active script run.
"""

from pathlib import Path
from runpy import run_path


APP_PATH = Path(__file__).parent / "smart_ai_file_organizer" / "streamlit_app.py"
run_path(str(APP_PATH), run_name="__main__")
