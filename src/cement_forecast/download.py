from __future__ import annotations

from pathlib import Path

import requests

from cement_forecast.data_catalog import DataSource


def download_file(source: DataSource, overwrite: bool = False, timeout: int = 60) -> Path:
    """Download one catalog source to its configured destination.

    Some official sources occasionally block automated access or change URLs.
    In those cases, manually download the file from `source.page_url` and place it at
    `source.destination`.
    """
    if source.download_url is None:
        raise ValueError(f"Source {source.key!r} has no direct download URL.")

    source.destination.parent.mkdir(parents=True, exist_ok=True)
    if source.destination.exists() and not overwrite:
        return source.destination

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; cement-forecast-guatemala/0.1; "
            "+https://github.com/)"
        )
    }
    response = requests.get(source.download_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    source.destination.write_bytes(response.content)
    return source.destination
