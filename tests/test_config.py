import json

import pytest

from smart_ai_file_organizer.config import ConfigError, load_config, save_config


def _valid_config():
    return {
        "categories": ["Finance", "Other"],
        "training_data": {
            "Finance": ["invoice payment bank tax"],
            "Other": ["manual guide general notes"],
        },
        "organizer": {"supported_extensions": [".txt"], "fallback_category": "Other"},
    }


def test_load_config_accepts_custom_path(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_valid_config()), encoding="utf-8")

    config = load_config(config_path)

    assert config["categories"] == ["Finance", "Other"]


def test_load_config_rejects_invalid_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(config_path)


def test_load_config_rejects_missing_training_data(tmp_path):
    config = _valid_config()
    del config["training_data"]["Finance"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ConfigError, match="Finance"):
        load_config(config_path)


def test_save_config_writes_requested_path_only(tmp_path):
    config_path = tmp_path / "local.json"
    save_config(_valid_config(), config_path)

    assert config_path.exists()
    assert load_config(config_path)["organizer"]["supported_extensions"] == [".txt"]
