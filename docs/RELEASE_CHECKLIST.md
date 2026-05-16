# Release Checklist

Use this checklist before tagging or publishing a showcase build.

## Verification

- [ ] `python -m ruff check .`
- [ ] `SMART_ORGANIZER_DISABLE_TRANSFORMERS=1 python -m pytest --cov=smart_ai_file_organizer --cov-report=term-missing --cov-report=xml`
- [ ] `python -m build`
- [ ] CLI smoke: dry-run a sample folder.
- [ ] CLI smoke: live move one disposable file, then undo it.
- [ ] Streamlit smoke: `streamlit run streamlit_app.py`.
- [ ] Desktop smoke: `smart-organizer-gui` launches and can run dry-run.

## Demo Assets

- [ ] Refresh `docs/media/demo.gif` from the current Streamlit app.
- [ ] Capture `docs/media/cli-safety-demo.png` showing dry-run, live history path, and undo.
- [ ] Capture `docs/media/desktop-gui.png` showing results plus low-confidence review.
- [ ] Confirm README image links render on GitHub.

## Release Notes

- [ ] Move `Unreleased` changelog entries under a version/date heading.
- [ ] Bump `version` in `pyproject.toml`.
- [ ] Confirm `.smart-organizer/`, `config.json`, logs, and search indexes stay ignored.

## Optional Windows Executable

The recommended install remains `pip install -e .`. For a local Windows demo
binary, install PyInstaller in a throwaway environment and run:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --name SmartOrganizer --onefile --windowed scripts/gui.py
```

Smoke-test the generated executable on a disposable folder before sharing it.
