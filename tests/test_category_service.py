import json

import pytest

from smart_ai_file_organizer.category_service import CategoryService, CategoryServiceError


def _config_path(tmp_path):
    config = {
        "categories": ["Finance", "Other"],
        "training_data": {
            "Finance": ["invoice payment bank"],
            "Other": ["manual guide"],
        },
        "organizer": {"supported_extensions": [".txt"], "fallback_category": "Other"},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_category_service_adds_category_with_keywords(tmp_path):
    service = CategoryService(_config_path(tmp_path))

    config = service.add_category("Travel", ["hotel flight passport"])

    assert "Travel" in config["categories"]
    assert config["training_data"]["Travel"] == ["hotel flight passport"]


def test_category_service_rejects_duplicate_category(tmp_path):
    service = CategoryService(_config_path(tmp_path))

    with pytest.raises(CategoryServiceError, match="already exists"):
        service.add_category("Finance")


def test_category_service_protects_other_category(tmp_path):
    service = CategoryService(_config_path(tmp_path))

    with pytest.raises(CategoryServiceError, match="fallback"):
        service.delete_category("Other")


def test_category_service_updates_keywords_from_text(tmp_path):
    service = CategoryService(_config_path(tmp_path))

    config = service.update_keywords("Finance", "invoice tax\n\nbank statement")

    assert config["training_data"]["Finance"] == ["invoice tax", "bank statement"]


def test_category_service_rejects_empty_keywords(tmp_path):
    service = CategoryService(_config_path(tmp_path))

    with pytest.raises(CategoryServiceError, match="At least one"):
        service.update_keywords("Finance", "   \n")
