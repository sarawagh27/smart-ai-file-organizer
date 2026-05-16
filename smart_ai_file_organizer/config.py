"""Configuration loading and validation for Smart AI File Organizer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config.json"
EXAMPLE_CONFIG = (
    PROJECT_ROOT / "config.example.json"
    if (PROJECT_ROOT / "config.example.json").exists()
    else PACKAGE_ROOT / "config.example.json"
)


class ConfigError(ValueError):
    """Raised when a configuration file exists but is not usable."""


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Return the explicit config path or the local/example fallback path."""
    if config_path is not None:
        path = Path(config_path).expanduser()
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        return path

    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    if EXAMPLE_CONFIG.exists():
        return EXAMPLE_CONFIG
    raise ConfigError(f"Config file not found: {DEFAULT_CONFIG} or {EXAMPLE_CONFIG}")


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate configuration without hiding malformed JSON."""
    path = resolve_config_path(config_path)
    try:
        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file {path}: {exc}") from exc

    validate_config(config, source=path)
    return config


def save_config(config: dict[str, Any], config_path: str | Path | None = None) -> None:
    """Validate and save configuration."""
    path = Path(config_path).expanduser() if config_path is not None else DEFAULT_CONFIG
    validate_config(config, source=path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def validate_config(config: dict[str, Any], source: Path | None = None) -> None:
    """Validate the minimum schema the app needs to behave predictably."""
    label = f" in {source}" if source else ""
    categories = config.get("categories")
    if not isinstance(categories, list) or not categories:
        raise ConfigError(f"Config{label} must define a non-empty 'categories' list.")
    if not all(isinstance(cat, str) and cat.strip() for cat in categories):
        raise ConfigError(f"Config{label} has invalid category names.")

    training_data = config.get("training_data")
    if not isinstance(training_data, dict) or not training_data:
        raise ConfigError(f"Config{label} must define non-empty 'training_data'.")

    missing = [
        cat for cat in categories
        if cat not in training_data or not isinstance(training_data[cat], list)
    ]
    if missing:
        raise ConfigError(
            f"Config{label} is missing training data lists for: {', '.join(missing)}"
        )

    organizer = config.get("organizer", {})
    if organizer and not isinstance(organizer, dict):
        raise ConfigError(f"Config{label} has invalid 'organizer' settings.")
    extensions = organizer.get("supported_extensions", [])
    if extensions and (
        not isinstance(extensions, list)
        or not all(isinstance(ext, str) and ext.startswith(".") for ext in extensions)
    ):
        raise ConfigError(f"Config{label} has invalid supported extensions.")
