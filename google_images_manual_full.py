from __future__ import annotations

"""
google_images_manual_full.py

Minimal Google Images scraper example using requests + BeautifulSoup
(tested conceptually around 2026-02-27 as a baseline).

Features:
- Start from a Google Images search URL (q + tbm=isch)
- Parse thumbnail image URLs and titles
- Optional localization via hl/gl
- Export data to CSV

This script is for small-scale, educational experiments only.
For robust, large-scale scraping, prefer Thordata's SERP API.
"""

import argparse
import random
from dataclasses import dataclass, asdict
from time import sleep
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup


SEARCH_URL = "https://www.google.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Referer": "https://www.google.com/",
}


session = requests.Session()


def safe_get(url: str, *, params: dict[str, Any] | None = None, max_retries: int = 3) -> requests.Response | None:
    """GET wrapper with basic retry and random backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, params=params, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
            print(f"[WARN] HTTP {resp.status_code} for {resp.url}, attempt {attempt}")
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            print(f"[ERROR] Network error on {url}, attempt {attempt}: {exc}")

        sleep_time = random.uniform(1.5, 3.5) * attempt
        print(f"[INFO] Sleeping {sleep_time:.1f}s before retry...")
        sleep(sleep_time)

    print(f"[ERROR] Failed to fetch {url} after {max_retries} attempts")
    return None


@dataclass
class ImageResult:
    title: str | None
    thumbnail_url: str | None


def fetch_google_images_html(
    query: str,
    *,
    hl: str = "en",
    gl: str = "us",
) -> str | None:
    params: dict[str, Any] = {
        "q": query,
        "tbm": "isch",
        "hl": hl,
        "gl": gl,
    }
    resp = safe_get(SEARCH_URL, params=params)
    if not resp:
        return None
    return resp.text


def parse_thumbnails(html: str) -> list[ImageResult]:
    """Parse thumbnail images from Google Images HTML."""
    soup = BeautifulSoup(html, "lxml")

    results: list[ImageResult] = []

    for img in soup.select("img"):
        alt = img.get("alt") or None
        src = img.get("data-src") or img.get("src") or None

        if not src:
            continue

        # Heuristic: skip obvious UI assets without alt text
        if "gstatic.com" in src and not alt:
            continue

        results.append(ImageResult(title=alt, thumbnail_url=src))

    return results


def save_images_to_csv(images: list[ImageResult], filename: str) -> None:
    if not images:
        print("[WARN] No images to save.")
        return
    df = pd.DataFrame([asdict(img) for img in images])
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(images)} images to {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal Google Images scraper (educational use only).")
    parser.add_argument("--query", required=True, help="Search query, e.g. 'cute cats'")
    parser.add_argument("--output", default="google_images.csv", help="Output CSV filename")
    parser.add_argument("--hl", default="en", help="Interface language code (default: en)")
    parser.add_argument("--gl", default="us", help="Country code for localization (default: us)")
    args = parser.parse_args()

    print(f"[INFO] Fetching Google Images HTML for query={args.query!r}, hl={args.hl}, gl={args.gl}")
    html = fetch_google_images_html(args.query, hl=args.hl, gl=args.gl)
    if html is None:
        print("[ERROR] Could not fetch Google Images HTML.")
        return

    print("[INFO] Parsing thumbnails from HTML...")
    images = parse_thumbnails(html)
    print(f"[INFO] Parsed {len(images)} candidate images")

    save_images_to_csv(images, args.output)


if __name__ == "__main__":
    main()

