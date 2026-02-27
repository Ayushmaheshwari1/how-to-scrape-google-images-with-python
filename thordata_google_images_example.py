from __future__ import annotations

"""
thordata_google_images_example.py

Example of using Thordata SERP API (google_images engine) via the official SDK.

Requirements:
    pip install thordata-sdk python-dotenv

Environment:
    Create a .env file with:
        THORDATA_SCRAPER_TOKEN=...
        THORDATA_PUBLIC_TOKEN=...
        THORDATA_PUBLIC_KEY=...
"""

import os
from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from thordata import ThordataClient


load_dotenv()


@dataclass
class GoogleImageItem:
    title: str | None
    image_url: str | None
    source_url: str | None


def google_images_search(
    query: str,
    *,
    country: str = "us",
    language: str = "en",
    page_number: int = 0,
    size_filter: str | None = None,
) -> list[GoogleImageItem]:
    """Call Thordata SERP API google_images engine and normalize key fields."""
    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    public_key = os.getenv("THORDATA_PUBLIC_KEY")

    if not scraper_token:
        raise RuntimeError("THORDATA_SCRAPER_TOKEN is required but not set")

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
    )

    params: dict[str, Any] = {
        "gl": country,
        "hl": language,
        "ijn": page_number,
        "json": 1,
    }
    if size_filter:
        params["imgsz"] = size_filter

    raw = client.serp.google.images(query, **params)

    items: list[GoogleImageItem] = []

    # Thordata JSON structure may evolve; handle common variants.
    images = raw.get("images_results") or raw.get("images") or []

    if not images:
        print(f"[DEBUG] No images_results/images in response. Top-level keys: {list(raw.keys())}")

    for img in images:
        title = img.get("title") or img.get("alt")
        image_url = img.get("original") or img.get("image")
        source_url = img.get("link") or img.get("source")

        if not image_url and not source_url:
            continue

        items.append(
            GoogleImageItem(
                title=title,
                image_url=image_url,
                source_url=source_url,
            )
        )

    return items


def save_results_to_csv(items: list[GoogleImageItem], filename: str) -> None:
    if not items:
        print("[WARN] No images to save to CSV.")
        return
    df = pd.DataFrame([asdict(it) for it in items])
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(items)} images to {filename}")


def save_preview_html(
    items: list[GoogleImageItem],
    filename: str = "thordata_google_images_preview.html",
    limit: int = 30,
    query: str | None = None,
) -> None:
    if not items:
        print("[WARN] No images to render in HTML preview.")
        return

    limited = [it for it in items if it.image_url][:limit]
    if not limited:
        print("[WARN] No image URLs available for HTML preview.")
        return

    title_text = f"Thordata Google Images Preview – {query!r}" if query else "Thordata Google Images Preview"

    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><meta charset='utf-8'>"
        f"<title>{title_text}</title></head>",
        "<body style='font-family:system-ui, -apple-system, BlinkMacSystemFont, sans-serif;'>",
        f"<h2>{title_text}</h2>",
        "<div style='display:flex;flex-wrap:wrap;gap:8px;'>",
    ]
    for it in limited:
        title = (it.title or "").replace('"', "&quot;")
        html_parts.append(
            f"<div style='max-width:220px;'>"
            f"<img src=\"{it.image_url}\" alt=\"{title}\" "
            f"style='max-width:200px;max-height:200px;display:block;border-radius:4px;'>"
            f"<div style='font-size:12px;margin-top:4px;'>{title}</div>"
            f"</div>"
        )
    html_parts.append("</div></body></html>")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    print(f"[INFO] Wrote HTML preview to {filename}")


def main() -> None:
    query = "cute cats"
    results = google_images_search(
        query,
        country="us",
        language="en",
        page_number=0,
        size_filter="qsvga",
    )

    print(f"Got {len(results)} images for query={query!r}")
    for item in results[:10]:
        print(f"- {item.title!r} | image={item.image_url} | source={item.source_url}")

    save_results_to_csv(results, "thordata_google_images.csv")
    save_preview_html(results, query=query)


if __name__ == "__main__":
    main()

