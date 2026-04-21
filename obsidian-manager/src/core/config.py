from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".notes-manager"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
LOGS_DIR = CONFIG_DIR / "logs"

_DEFAULT_CONFIG: dict[str, Any] = {
    "vault": {
        "path": "",
        "tags_file": "99_Служебная/Indexes/TAGS_HIERARCHICAL.md",
    },
    "folders": {
        "inbox": "00-inbox",
        "daily": "10-daily",
        "areas": "20-areas",
        "projects": "30-projects",
        "archive": "40-archive",
        "service": "99_Служебная",
        "attachments": "_attachments",
        "templates": "_templates",
    },
    "limits": {
        "max_notes_in_context": 25,
        "context_usage_threshold": 0.55,
        "search_max_results": 10,
    },
    "search": {
        "relevance_threshold": 0.2,
        "enable_backlink_expansion": True,
        "prioritization": ["backlink_count", "tag_match", "modification_date"],
    },
    "audit": {
        "min_note_length": 100,
        "check_untitled": True,
        "check_no_frontmatter": True,
        "default_untitled_names": ["Untitled", "Без названия", "New note"],
    },
    "profile": {
        "output_file": "CLAUDE.md",
        "sources": {
            "include_all": True,
            "exclude_tags": ["входящие/*", "архив/*"],
            "exclude_folders": ["99_Служебная"],
        },
        "analysis": {
            "depth": "deep",
            "time_window_months": None,
            "min_mentions_for_skill": 3,
            "extract_quotes": True,
            "show_contradictions": True,
        },
        "auto_update": {
            "enabled": True,
            "schedule": "monthly",
            "trigger_new_notes": 50,
        },
        "sections": [
            "basic_info",
            "technical_skills",
            "interests",
            "psychological_portrait",
            "communication_style",
            "current_context",
            "knowledge_map",
            "metadata",
            "changelog",
        ],
    },
}


class ConfigurationError(Exception):
    pass


@dataclass
class FoldersConfig:
    inbox: str = "00-inbox"
    daily: str = "10-daily"
    areas: str = "20-areas"
    projects: str = "30-projects"
    archive: str = "40-archive"
    service: str = "99_Служебная"
    attachments: str = "_attachments"
    templates: str = "_templates"


@dataclass
class LimitsConfig:
    max_notes_in_context: int = 25
    context_usage_threshold: float = 0.55
    search_max_results: int = 10


@dataclass
class SearchConfig:
    relevance_threshold: float = 0.2
    enable_backlink_expansion: bool = True
    prioritization: list[str] = field(default_factory=lambda: ["backlink_count", "tag_match", "modification_date"])


@dataclass
class AuditConfig:
    min_note_length: int = 100
    check_untitled: bool = True
    check_no_frontmatter: bool = True
    default_untitled_names: list[str] = field(default_factory=lambda: ["Untitled", "Без названия", "New note"])


@dataclass
class ProfileSourcesConfig:
    include_all: bool = True
    exclude_tags: list[str] = field(default_factory=lambda: ["входящие/*", "архив/*"])
    exclude_folders: list[str] = field(default_factory=lambda: ["99_Служебная"])


@dataclass
class ProfileAnalysisConfig:
    depth: str = "deep"
    time_window_months: int | None = None
    min_mentions_for_skill: int = 3
    extract_quotes: bool = True
    show_contradictions: bool = True


@dataclass
class ProfileConfig:
    output_file: str = "CLAUDE.md"
    sources: ProfileSourcesConfig = field(default_factory=ProfileSourcesConfig)
    analysis: ProfileAnalysisConfig = field(default_factory=ProfileAnalysisConfig)
    sections: list[str] = field(default_factory=lambda: [
        "basic_info", "technical_skills", "interests",
        "psychological_portrait", "communication_style",
        "current_context", "knowledge_map", "metadata", "changelog",
    ])


class Config:
    def __init__(self, data: dict[str, Any]) -> None:
        vault_data = data.get("vault", {})
        self.vault_path = Path(vault_data.get("path", "")) if vault_data.get("path") else None
        self.tags_file_relative = vault_data.get("tags_file", "99_Служебная/Indexes/TAGS_HIERARCHICAL.md")

        folders_data = data.get("folders", {})
        self.folders = FoldersConfig(**{k: v for k, v in folders_data.items() if k in FoldersConfig.__dataclass_fields__})

        limits_data = data.get("limits", {})
        self.limits = LimitsConfig(**{k: v for k, v in limits_data.items() if k in LimitsConfig.__dataclass_fields__})

        search_data = data.get("search", {})
        self.search = SearchConfig(**{k: v for k, v in search_data.items() if k in SearchConfig.__dataclass_fields__})

        audit_data = data.get("audit", {})
        self.audit = AuditConfig(**{k: v for k, v in audit_data.items() if k in AuditConfig.__dataclass_fields__})

        profile_data = data.get("profile", {})
        sources_data = profile_data.get("sources", {})
        analysis_data = profile_data.get("analysis", {})
        self.profile = ProfileConfig(
            output_file=profile_data.get("output_file", "CLAUDE.md"),
            sources=ProfileSourcesConfig(**{k: v for k, v in sources_data.items() if k in ProfileSourcesConfig.__dataclass_fields__}),
            analysis=ProfileAnalysisConfig(**{k: v for k, v in analysis_data.items() if k in ProfileAnalysisConfig.__dataclass_fields__}),
            sections=profile_data.get("sections", ProfileConfig.__dataclass_fields__["sections"].default_factory()),
        )

    def set_vault_path(self, path: str) -> None:
        self.vault_path = Path(path)

    @property
    def tags_file(self) -> Path | None:
        if self.vault_path is None:
            return None
        return self.vault_path / self.tags_file_relative


def setup_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "notes-manager.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("notes-manager")


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config() -> Config:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        _save_default_config()

    try:
        with CONFIG_FILE.open(encoding="utf-8") as f:
            user_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Ошибка чтения конфигурации: {e}") from e

    merged = _deep_merge(_DEFAULT_CONFIG, user_data)
    return Config(merged)


def _save_default_config() -> None:
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(_DEFAULT_CONFIG, f, allow_unicode=True, default_flow_style=False)


def save_config(config: Config) -> None:
    data = {
        "vault": {
            "path": str(config.vault_path) if config.vault_path else "",
            "tags_file": config.tags_file_relative,
        },
        "folders": {
            "inbox": config.folders.inbox,
            "daily": config.folders.daily,
            "areas": config.folders.areas,
            "projects": config.folders.projects,
            "archive": config.folders.archive,
            "service": config.folders.service,
            "attachments": config.folders.attachments,
            "templates": config.folders.templates,
        },
        "limits": {
            "max_notes_in_context": config.limits.max_notes_in_context,
            "context_usage_threshold": config.limits.context_usage_threshold,
            "search_max_results": config.limits.search_max_results,
        },
        "search": {
            "relevance_threshold": config.search.relevance_threshold,
            "enable_backlink_expansion": config.search.enable_backlink_expansion,
            "prioritization": config.search.prioritization,
        },
        "audit": {
            "min_note_length": config.audit.min_note_length,
            "check_untitled": config.audit.check_untitled,
            "check_no_frontmatter": config.audit.check_no_frontmatter,
            "default_untitled_names": config.audit.default_untitled_names,
        },
        "profile": {
            "output_file": config.profile.output_file,
        },
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
