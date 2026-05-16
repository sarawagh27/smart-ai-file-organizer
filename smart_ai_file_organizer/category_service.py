"""Testable category-management operations shared by GUI and future UIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_config, save_config


class CategoryServiceError(ValueError):
    """Raised when a category edit is invalid."""


@dataclass(frozen=True)
class CategoryService:
    config_path: str | Path

    def load(self) -> dict:
        return load_config(self.config_path)

    def list_categories(self) -> list[str]:
        return list(self.load().get("categories", []))

    def add_category(self, name: str, keywords: list[str] | None = None) -> dict:
        category = _clean_category_name(name)
        config = self.load()
        categories = config.setdefault("categories", [])
        if category in categories:
            raise CategoryServiceError(f"Category '{category}' already exists.")

        categories.append(category)
        config.setdefault("training_data", {})[category] = _clean_keywords(
            keywords or [f"add your keywords for {category} here"]
        )
        save_config(config, self.config_path)
        return config

    def delete_category(self, name: str) -> dict:
        category = _clean_category_name(name)
        if category == "Other":
            raise CategoryServiceError("'Other' is the fallback category and cannot be deleted.")

        config = self.load()
        categories = config.setdefault("categories", [])
        if category not in categories:
            raise CategoryServiceError(f"Category '{category}' does not exist.")

        categories.remove(category)
        config.setdefault("training_data", {}).pop(category, None)
        save_config(config, self.config_path)
        return config

    def update_keywords(self, name: str, text: str | list[str]) -> dict:
        category = _clean_category_name(name)
        config = self.load()
        if category not in config.get("categories", []):
            raise CategoryServiceError(f"Category '{category}' does not exist.")

        keywords = _clean_keywords(text)
        config.setdefault("training_data", {})[category] = keywords
        save_config(config, self.config_path)
        return config


def _clean_category_name(name: str) -> str:
    category = name.strip()
    if not category:
        raise CategoryServiceError("Category name is required.")
    return category


def _clean_keywords(text: str | list[str]) -> list[str]:
    if isinstance(text, str):
        keywords = [line.strip() for line in text.splitlines() if line.strip()]
    else:
        keywords = [line.strip() for line in text if line.strip()]
    if not keywords:
        raise CategoryServiceError("At least one keyword sentence is required.")
    return keywords
