from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin
from urllib.request import Request, urlopen


IMAE_2013_PAGE = (
    "https://banguat.gob.gt/page/"
    "indice-mensual-de-la-actividad-economica-imae-ano-de-referencia-2013"
)

FALLBACK_CUADROS_XLSX = (
    "https://banguat.gob.gt/sites/default/files/banguat/Publica/IMAE/2013/"
    "Cuadros_y_gr%C3%A1ficas_IMAE_mar2026.xlsx"
)


def _read_url(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def discover_current_imae_excel(page_url: str = IMAE_2013_PAGE) -> str:
    """Return the current Banguat IMAE statistical Excel URL.

    The Banguat page exposes several links. We prefer the workbook whose file name
    contains ``Cuadros`` because that workbook has the component tables used by
    ``parse_banguat_imae``. A fallback URL is kept because Banguat's site can be
    inconsistent when accessed programmatically.
    """
    try:
        html = _read_url(page_url).decode("utf-8", errors="ignore")
    except Exception:
        return FALLBACK_CUADROS_XLSX

    hrefs = re.findall(r'href=["\']([^"\']+\.xlsx)["\']', html, flags=re.IGNORECASE)
    urls = [urljoin(page_url, href) for href in hrefs]

    decoded_urls = [(url, unquote(url).lower()) for url in urls]

    preferred_patterns = [
        ("cuadros", "imae"),
        ("cuadros_y", "imae"),
        ("gráficas", "imae"),
        ("graficas", "imae"),
    ]

    for url, decoded in decoded_urls:
        if any(all(token in decoded for token in pattern) for pattern in preferred_patterns):
            return url

    return FALLBACK_CUADROS_XLSX


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = _read_url(url)
    destination.write_bytes(content)
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download the current Banguat IMAE 2013-reference Excel workbook. "
            "This avoids accidentally using the old 2001-reference workbook, "
            "which may stop around 2019."
        )
    )
    parser.add_argument(
        "--output",
        default="data/raw/banguat_imae_2013.xlsx",
        help="Destination path for the downloaded workbook.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Optional explicit Excel URL. If omitted, the script discovers the current URL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination = Path(args.output)
    url = args.url or discover_current_imae_excel()

    print(f"Downloading Banguat IMAE workbook from:\n{url}\n")

    try:
        path = download_file(url, destination)
    except Exception as exc:
        print(f"Failed to download {url}: {exc}", file=sys.stderr)
        if url != FALLBACK_CUADROS_XLSX:
            print("Trying fallback URL...", file=sys.stderr)
            path = download_file(FALLBACK_CUADROS_XLSX, destination)
        else:
            raise

    print(f"Saved: {path}")
    print("Next step:")
    print(
        "python scripts/build_modeling_dataset.py "
        "--source 'banguat_imae:data/raw/banguat_imae_2013.xlsx:IMAE componentes:6' "
        "--source 'ine_ipmc:data/raw/ine_ipmc_historico.xlsx:Publicación Histórico 2026:0' "
        "--skip-proxy-target"
    )


if __name__ == "__main__":
    main()
