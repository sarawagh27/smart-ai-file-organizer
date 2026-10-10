# Launch Checklist

Steps that need your GitHub / PyPI accounts, so they could not be done in the code.

## 1. GitHub repository settings (5 minutes)

- **Description:** `AI-powered file organizer: classify, rename, deduplicate and search documents by content. CLI, desktop GUI and Streamlit.`
- **Website:** `https://smart-ai-file-organizer.streamlit.app`
- **Topics:** `file-organizer`, `python`, `machine-learning`, `nlp`, `sentence-transformers`,
  `semantic-search`, `document-classification`, `duplicate-detection`, `streamlit`,
  `tkinter`, `automation`, `productivity`
- **Social preview:** Settings, then General, then Social preview, then upload
  `docs/media/social-preview.png`.

## 2. Release v0.2.0

1. Run the checks in `docs/RELEASE_CHECKLIST.md`.
2. `git tag v0.2.0 && git push origin v0.2.0`
3. On GitHub: Releases, Draft a new release, pick the tag, paste the `[0.2.0]` section of
   `docs/CHANGELOG.md`, attach `demo.gif`.

## 3. Publish to PyPI (so `pip install smart-ai-file-organizer` works)

1. Create an account on pypi.org and add a *pending trusted publisher*:
   owner `sarawagh27`, repo `smart-ai-file-organizer`, workflow `publish.yml`,
   environment `pypi`.
2. In the repo, create an environment named `pypi` (Settings, then Environments).
3. Publishing the GitHub release triggers `.github/workflows/publish.yml`.
4. Replace the editable install in the README Quick Start with `pip install smart-ai-file-organizer`.

## 4. Get it in front of people

- Post the demo GIF with a two-line pitch: r/Python, r/DataHoarder, r/selfhosted, LinkedIn.
- Lead with the safety story (dry-run, undo, hash-checked restore): that is what
  makes people trust a tool that moves their files.
- Share the measured accuracy table from the README rather than adjectives.
- Add the project to your GitHub profile README as a pinned repository.

## 5. Before sharing widely

- Run `python scripts/evaluate_classifier.py --transformer` once and add the result to
  the README accuracy table (the *AI model tests* workflow also reports it).
- Capture `docs/media/cli-safety-demo.png` and `docs/media/desktop-gui.png`.
- Rotate any NVIDIA API key that was ever committed or shown in a screenshot.
