from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cement_forecast.config import DATA_SOURCES_PATH, PROJECT_ROOT


@dataclass(frozen=True)
class DataSource:
    """Metadata for one source in the project data catalog."""

    key: str
    name: str
    page_url: str | None
    download_url: str | None
    destination: Path
    type: str
    frequency: str | None = None
    role: str | None = None


def load_data_sources(path: Path = DATA_SOURCES_PATH) -> dict[str, DataSource]:
    """Load the YAML data-source catalog."""
    with path.open("r", encoding="utf-8") as file:
        payload: dict[str, Any] = yaml.safe_load(file)

    sources = {}
    for key, raw in payload.get("sources", {}).items():
        destination = PROJECT_ROOT / raw["destination"]
        sources[key] = DataSource(
            key=key,
            name=raw.get("name", key),
            page_url=raw.get("page_url"),
            download_url=raw.get("download_url"),
            destination=destination,
            type=raw.get("type", "unknown"),
            frequency=raw.get("frequency"),
            role=raw.get("role"),
        )
    return sources
