# Contributing

Thanks for helping improve Smart AI File Organizer.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Install optional AI and web dependencies only when you need them:

```bash
python -m pip install -e ".[ai,web]"
```

## Tests

The default test suite runs in fast/offline mode and does not load the
sentence-transformers model.

```bash
python -m pytest
```

To test the transformer path manually, unset `SMART_ORGANIZER_DISABLE_TRANSFORMERS`
and install the `ai` extra.

## Pull requests

- Keep changes focused and reviewable.
- Do not commit `config.json`, API keys, local documents, logs, or generated indexes.
- Add or update tests for behavior changes.
- Run `python -m pytest` before opening a PR.
