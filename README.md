# How to Scrape Google Images With Python (2026 Edition)

> This repository is intentionally **minimal**: the main tutorial lives in this `README.md`, plus a single helper script.  
> All examples are tested so that you can copy, run, and adapt them for your own projects.

This guide is split into two parts, with the focus on a **free, reproducible tutorial**:

- **Part 1 (≈80%) – 100% free, manual scraping approach** using `requests + BeautifulSoup + lxml + pandas`.  
  We build a small script that can fetch **image title, thumbnail URL, full-size image URL (when available), and source page URL**, then export them to CSV.
- **Part 2 (≈20%) – Optional easier approach with Thordata SERP API** using Thordata’s Python SDK.  
  You send a query (e.g. `"cute cats"`), Thordata handles IP rotation and parsing, and you get back structured JSON for Google Images.

If you just want the final scripts, jump to:

- 🎯 Final manual script: `google_images_manual_full.py`
- 🚀 Thordata SERP API script: `thordata_google_images_example.py`

---

## Quickstart (TL;DR)

```bash
git clone https://github.com/Thordata/how-to-scrape-google-images-with-python.git
cd how-to-scrape-google-images-with-python
python -m venv .env && .env\Scripts\activate  # on Windows; adjust for macOS/Linux
pip install -r requirements.txt
```

**Run the free manual scraper:**

```bash
python google_images_manual_full.py --query "cute cats" --output manual_cute_cats.csv
```

**Run the Thordata SERP API example (after setting `.env`):**

```bash
python thordata_google_images_example.py
```

This will print a few results and create:

- `thordata_google_images.csv` – structured image data.
- `thordata_google_images_preview.html` – a simple HTML gallery you can open in your browser.

---

## Contents

- [Setup](#setup)
  - [Create a virtual environment](#create-a-virtual-environment)
  - [Install dependencies](#install-dependencies)
- [Part 1 – Free manual Google Images scraping](#part-1--free-manual-google-images-scraping)
  - [1. First naive request and why it often fails](#1-first-naive-request-and-why-it-often-fails)
  - [2. Sending browser-like headers](#2-sending-browser-like-headers)
  - [3. Inspecting Google Images HTML structure](#3-inspecting-google-images-html-structure)
  - [4. Parsing image results into a Python dict](#4-parsing-image-results-into-a-python-dict)
  - [5. Exporting results to CSV](#5-exporting-results-to-csv)
  - [6. Adding basic retry and throttling](#6-adding-basic-retry-and-throttling)
  - [🎯 Final manual scraper script](#-final-manual-scraper-script)
- [Legal and compliance notice](#legal-and-compliance-notice)
- [Part 2 – 🚀 Easier solution with Thordata SERP API](#part-2--easier-solution-with-thordata-serp-api)
  - [1. Installation and authentication](#1-installation-and-authentication)
  - [2. Example: Google Images search via Thordata SDK](#2-example-google-images-search-via-thordata-sdk)
  - [3. Mapping common Google Images filters](#3-mapping-common-google-images-filters)
  - [4. Manual vs. Thordata comparison](#4-manual-vs-thordata-comparison)
- [Related Thordata resources](#related-thordata-resources)

---

## Setup

### Create a virtual environment

**macOS / Linux:**

```bash
mkdir google-images-tutorial && cd google-images-tutorial
python3 -m venv .env
source .env/bin/activate
```

**Windows (PowerShell or cmd):**

```bash
mkdir google-images-tutorial
cd google-images-tutorial
python -m venv .env
.env\Scripts\activate
```

### Install dependencies

We’ll use a few common free libraries:

```bash
pip install requests beautifulsoup4 lxml pandas
```

Quick sanity check:

```bash
python -c "import requests, bs4, lxml, pandas; print('ok')"
```

---

## Part 1 – Free manual Google Images scraping

This part shows **how to scrape Google Images manually** with nothing but free Python libraries.  
It is intentionally explicit so you see each moving part: HTTP request, HTML structure, parsing, and export.

> ⚠️ Disclaimer: Google actively protects against automated scraping.  
> The code below is for **learning and small‑scale experiments only**.  
> For production, high‑volume, or commercial use, consider a dedicated, compliant scraping solution (see the Thordata section below).

### 1. First naive request and why it often fails

Create a file `google_images_manual.py` with the simplest possible request:

```python
import requests

query = "cute cats"
url = "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(query)

resp = requests.get(url, timeout=30)

print(resp.status_code)
print(resp.text[:500])
```

Run it:

```bash
python google_images_manual.py
```

Common outcomes:

- You may see status code `200`, but the HTML is a consent page, captcha, or a page asking you to enable JavaScript.
- Sometimes the response is localized, and layout differs from what you see in your browser.

This happens because:

- Requests from a plain script lack typical **browser headers** and cookies.
- Google adjusts content based on many signals (region, language, cookies, JS, etc.).

### 2. Sending browser-like headers

To reduce the chance of being served a consent or interstitial page, mimic a real browser:

```python
import requests

query = "cute cats"
url = "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(query)

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

resp = requests.get(url, headers=HEADERS, timeout=30)
print(resp.status_code)
print(resp.text[:500])
```

At this point, if you open the same query in a browser (logged‑out, in a private window) and compare, you should see similar HTML structure in most cases.

> This still does **not** bypass all protections. It only makes your request look more like a normal browser visit.

### 3. Inspecting Google Images HTML structure

Open your browser and:

1. Go to `https://www.google.com/imghp`.
2. Search for `cute cats`.
3. Open DevTools (F12) → **Elements** tab.
4. Hover over several image tiles and inspect the DOM.

Typically you’ll see:

- A top-level container for image tiles.
- For each result, a wrapper element that contains:
  - A thumbnail `<img>` tag (small preview).
  - A link to the **source page**.
  - Metadata like title / alt text, often in nearby tags or data attributes.

The exact HTML changes over time, but the idea is:

- Find the **repeatable tile element**.
- Within each tile, extract:
  - Human-readable title or alt text.
  - Thumbnail URL.
  - Link to the source page (the page where the image is hosted).

We’ll keep our parsing logic **defensive** and accept that some fields may be missing or move as Google updates the layout.

### 4. Parsing image results into a Python dict

Let’s put this together in a small helper function:

```python
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

import requests
from bs4 import BeautifulSoup


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


@dataclass
class ImageResult:
    title: str | None
    thumb_url: str | None
    source_page: str | None
    query: str


def fetch_google_images_html(query: str) -> str:
    url = "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(query)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_image_results(html: str, query: str) -> List[ImageResult]:
    soup = BeautifulSoup(html, "lxml")

    results: list[ImageResult] = []

    # Google frequently uses <a> or <div> wrappers for each tile.
    # We keep this logic conservative and limited to a few simple patterns.
    tiles = soup.select("a[jsname][href] img") or soup.select("a[href] img")

    seen: set[tuple[str | None, str | None]] = set()

    for img in tiles:
        thumb_url = img.get("src") or img.get("data-src")
        title = img.get("alt") or img.get("data-alt")

        parent_link = img.find_parent("a")
        source_page = parent_link.get("href") if parent_link else None

        key = (thumb_url, source_page)
        if key in seen:
            continue
        seen.add(key)

        if not thumb_url and not source_page:
            continue

        results.append(
            ImageResult(
                title=title.strip() if isinstance(title, str) else None,
                thumb_url=thumb_url,
                source_page=source_page,
                query=query,
            )
        )

    return results
```

Test it quickly:

```python
if __name__ == "__main__":
    html = fetch_google_images_html("cute cats")
    images = parse_image_results(html, "cute cats")
    print(f"Got {len(images)} image results")
    for img in images[:5]:
        print(img)
```

If you see a list of `ImageResult(...)` objects with thumbnail URLs and source links, the basic parser is working.

### 5. Exporting results to CSV

We can convert our dataclasses into a `pandas` DataFrame:

```python
import pandas as pd


def save_images_to_csv(results: list[ImageResult], filename: str) -> None:
    if not results:
        print("[WARN] No image results to save.")
        return
    df = pd.DataFrame([asdict(r) for r in results])
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(results)} rows to {filename}")
```

Usage:

```python
if __name__ == "__main__":
    query = "cute cats"
    html = fetch_google_images_html(query)
    images = parse_image_results(html, query)
    save_images_to_csv(images, "google_images_cute_cats.csv")
```

You should find a CSV file in your working directory with at least:

- `title`
- `thumb_url`
- `source_page`
- `query`

### 6. Adding basic retry and throttling

For manual scraping, the biggest issues are:

- Occasional non‑200 responses or interstitial pages.
- Rate limiting or temporary blocks if you send too many requests too quickly.

A tiny retry wrapper helps:

```python
import random
from time import sleep

import requests


session = requests.Session()


def safe_get(url: str, max_retries: int = 3, **kwargs) -> requests.Response:
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=30, **kwargs)
            if resp.status_code == 200:
                return resp
            print(f"[WARN] HTTP {resp.status_code} for {url}, attempt {attempt}")
        except requests.RequestException as e:
            print(f"[ERROR] Network error on {url}, attempt {attempt}: {e}")

        sleep_time = random.uniform(1.5, 3.0) * attempt
        print(f"[INFO] Sleeping {sleep_time:.1f}s before retry...")
        sleep(sleep_time)

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")
```

Then in `fetch_google_images_html`:

```python
def fetch_google_images_html(query: str) -> str:
    url = "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(query)
    resp = safe_get(url, headers=HEADERS)
    return resp.text
```

---

### 🎯 Final manual scraper script

Below is a **complete** minimal script (`google_images_manual_full.py`) that:

- Accepts a query string.
- Fetches the first Google Images results page.
- Parses thumbnail URL, source page URL, and title where available.
- Exports everything to CSV.

> ⚠️ Again, this is for **small‑scale experiments only**.  
> It does not bypass all of Google’s protections, nor does it guarantee stable layouts.

Copy this into `google_images_manual_full.py` in this repository, or into your own project:

```python
from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from time import sleep
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup


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


def safe_get(url: str, max_retries: int = 3, **kwargs) -> requests.Response:
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=30, **kwargs)
            if resp.status_code == 200:
                return resp
            print(f"[WARN] HTTP {resp.status_code} for {url}, attempt {attempt}")
        except requests.RequestException as e:
            print(f"[ERROR] Network error on {url}, attempt {attempt}: {e}")

        sleep_time = random.uniform(1.5, 3.0) * attempt
        print(f"[INFO] Sleeping {sleep_time:.1f}s before retry...")
        sleep(sleep_time)

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")


@dataclass
class ImageResult:
    title: str | None
    thumb_url: str | None
    source_page: str | None
    query: str


def fetch_google_images_html(query: str) -> str:
    url = "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(query)
    print(f"[INFO] Fetching Google Images HTML for query={query!r}")
    resp = safe_get(url, headers=HEADERS)
    return resp.text


def parse_image_results(html: str, query: str) -> List[ImageResult]:
    soup = BeautifulSoup(html, "lxml")

    # Basic bot/consent detection: if we don't see any <img> tiles, save HTML for inspection.
    tiles = soup.select("a[jsname][href] img") or soup.select("a[href] img")
    print(f"[INFO] Found {len(tiles)} candidate <img> elements")

    if not tiles:
        debug_name = "debug_google_images_page.html"
        try:
            with open(debug_name, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[WARN] No tiles detected, saved HTML snapshot to {debug_name}")
        except Exception as e:
            print(f"[WARN] Failed to save debug HTML: {e}")

    results: list[ImageResult] = []
    seen: set[tuple[str | None, str | None]] = set()

    for img in tiles:
        thumb_url = img.get("src") or img.get("data-src")
        title = img.get("alt") or img.get("data-alt")

        parent_link = img.find_parent("a")
        source_page = parent_link.get("href") if parent_link else None

        key = (thumb_url, source_page)
        if key in seen:
            continue
        seen.add(key)

        if not thumb_url and not source_page:
            continue

        results.append(
            ImageResult(
                title=title.strip() if isinstance(title, str) else None,
                thumb_url=thumb_url,
                source_page=source_page,
                query=query,
            )
        )

    return results


def save_images_to_csv(results: list[ImageResult], filename: str) -> None:
    if not results:
        print("[WARN] No image results to save.")
        return
    df = pd.DataFrame([asdict(r) for r in results])
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(results)} rows to {filename}")


def main() -> None:
    query = "cute cats"
    html = fetch_google_images_html(query)
    results = parse_image_results(html, query)
    print(f"[INFO] Parsed {len(results)} image results")
    save_images_to_csv(results, "google_images_cute_cats.csv")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python google_images_manual_full.py
```

If things go well, you’ll see logs followed by a `google_images_cute_cats.csv` file with a set of images and source pages.

---

## Legal and compliance notice

- The code in this repository is for **technical learning and research only**.
- Always respect the target website’s **Terms of Service** and applicable laws.
- Keep your scraping frequency low, use appropriate headers, and avoid putting unnecessary load on any site.
- For production, commercial, or large‑scale use cases, strongly consider using a dedicated, compliant scraping API.

---

## Part 2 – 🚀 Easier solution with Thordata SERP API

The manual approach has clear limitations:

- You are responsible for:
  - Navigating consent / captcha / interstitial pages.
  - Keeping up with HTML layout changes.
  - Handling retries, IP reputation, and throttling.
- Parsing logic is **fragile** and must be updated when Google tweaks its DOM.

Thordata’s SERP API wraps Google Images in a stable, structured API:

- You send a request with:
  - `engine=google_images`
  - `q=your_query`
  - Optional filters like `gl`, `hl`, `ijn`, `imgsz`, `licenses`, etc.  
    (see the Google Images parameter reference inside Thordata docs / SDK)
- Thordata handles:
  - IP rotation & anti‑bot mitigation.
  - Retrying and timeouts.
  - Parsing the response into JSON.

### 1. Installation and authentication

**Install the Thordata SDK:**

```bash
pip install thordata-sdk python-dotenv
```

**Create a `.env` file** next to your script:

```ini
THORDATA_SCRAPER_TOKEN=your_scraper_token
THORDATA_PUBLIC_TOKEN=your_public_token
THORDATA_PUBLIC_KEY=your_public_key
```

You can find these values in your Thordata Dashboard.  
For a quick guided reference, see the official `thordata-python-sdk` repository.

### 2. Example: Google Images search via Thordata SDK

Create a new file `thordata_google_images_example.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

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
    """
    Call Thordata SERP API for Google Images and normalize a few key fields.
    """
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

    # Map high-level options to Google Images parameters.
    params: dict[str, Any] = {
        "gl": country,  # country
        "hl": language,  # UI language
        "ijn": page_number,  # images page index (0-based)
        "json": 1,
    }

    # Optional image size filter (maps to imgsz).
    if size_filter:
        params["imgsz"] = size_filter

    raw = client.serp.google.images(query, **params)

    results: list[GoogleImageItem] = []

    # The exact JSON keys may evolve; this logic is based on current Thordata docs.
    images = raw.get("images_results") or raw.get("images") or []

    if not images:
        print(f"[DEBUG] No images_results/images in response. Top-level keys: {list(raw.keys())}")

    for img in images:
        title = img.get("title") or img.get("alt")
        image_url = img.get("original") or img.get("image")
        source_url = img.get("link") or img.get("source")

        if not image_url and not source_url:
            continue

        results.append(
            GoogleImageItem(
                title=title,
                image_url=image_url,
                source_url=source_url,
            )
        )

    return results


def main() -> None:
    query = "cute cats"
    items = google_images_search(
        query,
        country="us",
        language="en",
        page_number=0,
        size_filter="qsvga",  # e.g. larger than 400×300
    )

    print(f"Got {len(items)} images for query={query!r}")
    for item in items[:5]:
        print(f"- {item.title!r} | image={item.image_url} | source={item.source_url}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python thordata_google_images_example.py
```

You should see a concise list of images, each with:

- A human-readable title (if available).
- A direct image URL.
- A source page URL.

Under the hood, this is using:

- `engine=google_images`
- `q=<your query>`
- `gl`, `hl`, `ijn`, `imgsz`, and `json=1`

The parameter mapping follows the Thordata SERP API docs for Google Images (localization, geotargeting, time period, pagination, and advanced filters).

### 3. Mapping common Google Images filters

Thordata’s SERP API supports most of the familiar Google Images filters using parameters such as:

- **Localization & language**
  - `google_domain`: which Google domain to use, e.g. `google.com`, `google.co.jp`.
  - `gl`: country (two-letter code), e.g. `us`, `ru`.
  - `hl`: UI language, e.g. `en`, `es`, `zh-CN`.
  - `cr`: multiple countries, like `countryFR|countryDE`.
- **Time period**
  - `period_unit`: unit for time (`s`, `n`, `h`, `d`, `w`, `m`, `y`).
  - `period_value`: number for the chosen unit (e.g. `7` for 7 days).
  - `start_date` / `end_date`: date range in `YYYYMMDD` format.
- **Pagination**
  - `ijn`: images page index (0-based, 100 images per page).
- **Advanced filters**
  - `chips`: recommended search refinements from `suggested_searches`.
  - `tbs`: advanced search parameters string.
  - `imgar`: aspect ratio (`s`, `t`, `w`, `xw`).
  - `imgsz`: size (`l`, `m`, `i`, `qsvga`, `vga`, `svga`, `xga`, `2mp`, …).
  - `image_color`: color filter (`bw`, `red`, `blue`, …).
  - `image_type`: `face`, `photo`, `clipart`, `lineart`, `animated`.
  - `licenses`: usage rights (`f`, `fc`, `fm`, `fmc`, `cl`, `ol`).
  - `safe`: safe search (`active`, `off`).
  - `nfpr`: exclude auto-corrected results.
  - `filter`: enable/disable “Similar/Omitted results” filters.

You can pass any of these directly through the Thordata SDK by adding extra keyword arguments to `client.serp.google.images(...)`.  
For example, to search for large, red images of pizza in the last 7 days:

```python
images = client.serp.google.images(
    "pizza",
    gl="us",
    hl="en",
    period_unit="d",
    period_value=7,
    imgsz="l",
    image_color="red",
    json=1,
)
```

### 4. Manual vs. Thordata comparison

| Aspect                | Manual free approach (Part 1)                                | Thordata SERP API approach                                          |
|-----------------------|--------------------------------------------------------------|----------------------------------------------------------------------|
| Anti‑bot handling     | You handle blocks, captchas, and retries yourself           | Handled by Thordata’s infrastructure                                |
| Parsing maintenance   | DOM/layout change ⇒ update selectors and parsing code        | Thordata maintains parsers; you keep consuming stable JSON          |
| Dev effort            | You write/maintain all HTTP, parsing, and CSV logic         | You focus on query parameters and how to use the structured result  |
| Learning value        | High – you learn HTTP, HTML structure, and anti‑bot basics  | Medium – closer to real‑world data pipelines                        |
| Best use cases        | Small experiments, personal learning                        | Commercial, large‑scale, or reliability‑focused scraping            |

A common workflow:

1. **Prototype** with the free manual scripts to understand what data you need from Google Images.
2. When you’re ready for something more stable or larger scale, **switch to Thordata SERP API**.
3. Plug the Thordata results into your analytics stack, image pipelines, or downstream AI workflows.

---

## Related Thordata resources

- Thordata Python SDK: search for `thordata-python-sdk` on GitHub.  
- Thordata official documentation: see the SERP API / Google Images parameter reference for the most up-to-date filter list.  
- Other example repositories in the Thordata ecosystem (Amazon, Google Maps, Google News, etc.) show similar “80% free tutorial + 20% Thordata” patterns you can reuse.

# How to Scrape Google Images With Python (2026 Edition)

> This repository intentionally keeps the structure **minimal** so you can clone it and follow along step‑by‑step.  
> All runnable examples live in this `README.md` and a single Python script file.

This guide is split into two parts, following a **teaching‑first** philosophy:

- **Part 1 (≈80%) – 100% free, manual scraping approach** using `requests + BeautifulSoup + lxml + pandas`.  
  We’ll build a script that sends a normal Google Images request, parses thumbnails and full‑size image URLs, and saves results into CSV.
- **Part 2 (≈20%) – Optional easier approach with Thordata** using Thordata’s SERP API & Python SDK, where IP rotation, retries, and parsing are handled in the cloud and you receive structured JSON for Google Images.

If you just want the final full script, jump to:

- 🎯 Final manual script: `google_images_manual_full.py`
- 🚀 Easier solution with Thordata: `thordata_google_images_demo.py`

---

## Part 0 – Setup

### Create a virtual environment

**macOS / Linux:**

```bash
python3 -m venv .env
source .env/bin/activate
```

**Windows:**

```bash
python -m venv .env
.env\Scripts\activate
```

> Tip: it’s a good idea to create a dedicated folder for this tutorial:
>
> ```bash
> mkdir google-images-tutorial && cd google-images-tutorial
> ```

### Install dependencies

For the free part we only need a few common libraries:

```bash
pip install requests beautifulsoup4 lxml pandas
```

Quick sanity check:

```bash
python -c "import requests, bs4, lxml, pandas; print('ok')"
```

For the optional Thordata section, we’ll additionally use:

```bash
pip install thordata-sdk python-dotenv
```

You can also install everything at once:

```bash
pip install -r requirements.txt
```

---

## Part 1 – Free manual Google Images scraping (Requests + BeautifulSoup)

This part focuses on **how Google Images works at the HTTP/HTML level** using nothing but free Python libraries.  
It is intentionally explicit so you can see all the moving parts and adapt it to your own experiments.

### 1. Understanding the Google Images URL

Open a browser and search for any query on Google Images, for example:

- Search bar: `cute cats`
- Then switch to the **Images** tab.

You’ll see a URL similar to:

```text
https://www.google.com/search?q=cute+cats&tbm=isch
```

Key pieces:

- `q=cute+cats` – your search query.
- `tbm=isch` – tells Google “this is an image search”.

We can send the same request from Python, but we must add **browser‑like headers** to avoid obvious bot detection.

### 2. First request with minimal headers

Create a file `google_images_step1.py`:

```python
import requests

url = "https://www.google.com/search"
params = {
    "q": "cute cats",
    "tbm": "isch",  # image search
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
print(resp.status_code)
print(resp.text[:1000])
```

Run it:

```bash
python google_images_step1.py
```

If everything is fine, status code should be `200` and the body will contain a large HTML page with many `<img>` tags and some embedded JSON blobs.

If you see lots of JavaScript about unusual traffic or captchas, slow down your request rate or retry from a residential IP/network.

### 3. Inspecting image elements in DevTools

In your browser:

1. Open Google Images for `cute cats`.
2. Press `F12` to open DevTools.
3. Go to the **Elements** tab.
4. Hover over thumbnails to find the `<img>` tags.

Typical patterns:

- Grid thumbnails often live inside containers with `data-ri` or other numeric attributes.
- The image URL can be found in `src` or `data-src` / `data-iurl` depending on layout and lazy‑loading.

We’ll focus on two pieces of data per image:

- A human‑readable `alt` or title text.
- A URL to the image (thumbnail or full‑size).

### 4. Parsing thumbnails with BeautifulSoup

Create `google_images_step2.py`:

```python
from __future__ import annotations

from typing import Any

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
}


def fetch_google_images_html(query: str, extra_params: dict[str, Any] | None = None) -> str:
    params: dict[str, Any] = {
        "q": query,
        "tbm": "isch",  # image search
    }
    if extra_params:
        params.update(extra_params)

    resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_thumbnails(html: str) -> list[dict[str, str | None]]:
    """
    Very simple thumbnail parser:
    - looks for <img> tags inside Google Images results
    - extracts alt text and src/data-src
    """
    soup = BeautifulSoup(html, "lxml")

    results: list[dict[str, str | None]] = []

    for img in soup.select("img"):
        alt = img.get("alt") or None
        src = img.get("data-src") or img.get("src") or None

        # Skip logos and empty thumbnails
        if not src:
            continue
        if "gstatic.com" in src and not alt:
            # Probably Google UI assets (logos, icons)
            continue

        results.append(
            {
                "title": alt,
                "thumbnail_url": src,
            }
        )

    return results


if __name__ == "__main__":
    html = fetch_google_images_html("cute cats")
    images = parse_thumbnails(html)
    print(f"Found {len(images)} images")
    for item in images[:5]:
        print(item)
```

Run:

```bash
python google_images_step2.py
```

You should see a count of images and a few thumbnail URLs printed to the console.

### 5. Saving data to CSV

Add a simple helper with `pandas`:

```python
import pandas as pd


def save_images_to_csv(
    items: list[dict[str, str | None]], filename: str = "google_images.csv"
) -> None:
    if not items:
        print("[WARN] No images to save.")
        return
    df = pd.DataFrame(items)
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(items)} rows to {filename}")
```

You can integrate this into your `__main__` section:

```python
if __name__ == "__main__":
    html = fetch_google_images_html("cute cats")
    images = parse_thumbnails(html)
    save_images_to_csv(images, "cute_cats_images.csv")
```

After running the script, you should see a `cute_cats_images.csv` file in your directory with two columns:

- `title`
- `thumbnail_url`

### 6. Handling basic filters and localization

Google Images exposes many filters, which map to URL parameters such as:

- `hl` – interface language.
- `gl` – country.
- `tbs` – advanced filters (size, color, type, time range, etc.).

For example, to restrict results to large images only, you can set a `tbs` parameter similar to:

```python
html = fetch_google_images_html(
    "cute cats",
    extra_params={
        "tbs": "isz:l",  # large images
    },
)
images = parse_thumbnails(html)
save_images_to_csv(images, "cute_cats_large.csv")
```

> ⚠️ Google’s internal `tbs` values change over time and are not officially documented.  
> A more stable way to use advanced filters is via a SERP API like Thordata’s, which exposes documented parameters such as `imgsz`, `image_color`, `image_type`, `licenses`, etc.  
> See the Thordata Google Images parameter reference in your local docs (`.ai/SERP API参数/Google/8Google Images.md`) for the full list.

### 7. Adding simple retry & rate limiting

As with any scraping against large websites, you should:

- Keep your request frequency low.
- Add random delays.
- Implement a small retry loop for transient network issues.

In the **final script** we’ll include:

- A shared `requests.Session`.
- A `safe_get` wrapper with basic retry and backoff.
- Throttling between requests.

### 🎯 Final manual script – `google_images_manual_full.py`

The file `google_images_manual_full.py` in this repository contains a **complete**, runnable example that:

- Sends a Google Images search for a given query.
- Parses thumbnail image URLs and titles.
- Supports optional language/country parameters.
- Saves results into a CSV file.

You can run it directly:

```bash
python google_images_manual_full.py --query "cute cats" --output cute_cats.csv
```

> This script is meant for **small‑scale, educational experiments**.  
> For anything approaching production scale, consider using Thordata’s SERP API described in Part 2 below.

---

## Part 2 – 🚀 Easier Google Images scraping with Thordata SERP API (optional)

The manual approach has several inherent drawbacks:

- You manage headers, cookies, and IP reputation yourself.
- HTML structure can change without notice and break your parser.
- Advanced filters (size, color, time, usage rights) require reverse‑engineering `tbs` values.

Thordata’s SERP API solves these problems by providing:

- An officially supported Google Images engine: `engine=google_images`.
- Clear, documented parameters such as:
  - `q` – query.
  - `gl`, `hl`, `cr`, `location`, `uule` – localization and geotargeting.
  - `imgsz`, `imgar`, `image_color`, `image_type`, `licenses`, `safe`, `filter`, `nfpr`, etc.
  - `ijn` – page number for images (100 images per page).

The Thordata Python SDK wraps these into a familiar interface so you can focus on **what** to fetch, not **how** to stay unblocked.

### 1. Install SDK and configure credentials

Install:

```bash
pip install thordata-sdk python-dotenv
```

Create a `.env` file in your project root (or reuse any existing one from other Thordata examples) and fill in your credentials:

```ini
THORDATA_SCRAPER_TOKEN=your_scraper_token
THORDATA_PUBLIC_TOKEN=your_public_token
THORDATA_PUBLIC_KEY=your_public_key
```

> You can find the exact variable names and meaning in the official `thordata-python-sdk` repository’s `.env.example`.  
> Never commit your `.env` file to Git.

### 2. Basic Google Images search via Thordata SDK

Create `thordata_google_images_demo.py`:

```python
from __future__ import annotations

from typing import Any

from thordata import ThordataClient, load_env_file


def search_google_images_with_thordata(
    query: str,
    *,
    gl: str = "us",
    hl: str = "en",
    ijn: int = 0,
    **extra_params: Any,
) -> dict[str, Any]:
    """Call Thordata SERP API for Google Images and return the raw JSON."""

    # Load .env if present (does not override existing env vars)
    load_env_file()

    client = ThordataClient()

    # Under the hood this sends:
    #   engine=google_images, q=query, gl=..., hl=..., ijn=..., json=1, ...
    data = client.serp.google.images(
        query,
        gl=gl,
        hl=hl,
        ijn=ijn,
        json=1,
        **extra_params,
    )
    return data


if __name__ == "__main__":
    results = search_google_images_with_thordata(
        "cute cats",
        imgsz="qsvga",       # similar to "larger than 400x300"
        image_type="photo",  # photos only
        safe="active",       # filter explicit content
    )

    # Print how many images we got in the first page
    images = results.get("images_results") or results.get("images", [])
    print(f"Total images: {len(images)}")
    if images:
        first = images[0]
        print(
            {
                "title": first.get("title"),
                "thumbnail": first.get("thumbnail"),
                "original": first.get("original"),
                "source": first.get("source"),
            }
        )
```

With a valid `.env` and network access, you should see a count of images and a compact dictionary describing the first result.

Behind the scenes:

- The SDK sends a POST request to `https://scraperapi.thordata.com/request`.
- `engine` is set to `google_images`.
- Extra parameters like `imgsz`, `image_type`, `licenses`, `safe`, etc. are passed through exactly as described in the Thordata Google Images parameter reference (`8Google Images.md`).

### 3. Extracting a clean CSV from Thordata’s JSON

The exact JSON schema may evolve, but a typical Google Images response contains a list such as `images_results` or `images`.  
We can normalize it into a tabular format:

```python
import pandas as pd


def export_thordata_images_to_csv(results: dict, filename: str) -> None:
    images = results.get("images_results") or results.get("images") or []
    rows = []
    for pos, img in enumerate(images, start=1):
        rows.append(
            {
                "position": pos,
                "title": img.get("title"),
                "original_url": img.get("original") or img.get("image"),
                "thumbnail_url": img.get("thumbnail"),
                "source_page": img.get("source") or img.get("link"),
                "domain": img.get("domain"),
            }
        )

    if not rows:
        print("[WARN] No image rows found in Thordata response.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"[INFO] Saved {len(rows)} images to {filename}")
```

You can integrate this with the previous demo:

```python
if __name__ == "__main__":
    results = search_google_images_with_thordata(
        "cute cats",
        imgsz="qsvga",
        image_type="photo",
        safe="active",
        ijn=0,
    )
    export_thordata_images_to_csv(results, "thordata_cute_cats.csv")
```

Now you have a **fully structured CSV** with positions, titles, original image URLs, thumbnails, and source pages, without maintaining fragile HTML parsers.

### 4. Manual vs. Thordata comparison

| Aspect               | Manual free approach (Part 1)                              | Thordata SERP API approach (Part 2)                                       |
|----------------------|------------------------------------------------------------|----------------------------------------------------------------------------|
| Anti‑bot handling    | Depends on your IP, headers, timing                        | IP pool, retries, rate limiting, and anti‑bot handling built‑in           |
| Parsing maintenance  | HTML changes ⇒ update selectors and parsing logic          | Thordata maintains the integration; you consume stable JSON               |
| Advanced filters     | Reverse‑engineer `tbs` and undocumented params             | Use documented fields (`imgsz`, `image_color`, `image_type`, `licenses`)  |
| Development effort   | You build and maintain all requests/parsers                | You focus on query design and downstream data usage                       |
| Best use cases       | Small experiments, personal learning, prototyping          | Commercial, large‑scale, or mission‑critical scraping & analytics         |

A common workflow is:

1. Use the **manual scripts** in this repo to understand how Google Images pages are structured and what data you need.
2. Once your schema is stable, switch to **Thordata SERP API** for robust, repeatable pipelines (and manage everything from the Thordata Dashboard).

---

## Legal and compliance notice

- This repository is for **technical learning and experimentation only**.
- Always respect Google’s **Terms of Service** and applicable laws in your jurisdiction.
- Keep request frequency low, cache results when possible, and avoid putting excessive load on Google’s infrastructure.
- For commercial or large‑scale usage, prefer using a specialized, compliant scraping platform such as Thordata’s SERP API and Dashboard, which are designed with **rate limiting, monitoring, and account‑level controls**.

