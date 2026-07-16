from pathlib import Path

from utils import (
    RAW_DIR,
    load_json,
    normalize_url,
    parse_sitemap,
    percentage
)

SITEMAP_URL = "https://www.srmist.edu.in/sitemap.xml"

WEBSITE_FILES = [
    RAW_DIR / "ktr_website_data.json",
    RAW_DIR / "new_scraped_data.json",
]


def load_scraped_records():
    records = []

    for file in WEBSITE_FILES:
        data = load_json(file)

        if isinstance(data, list):
            records.extend(data)

    return records


def audit_website():
    print("\nAuditing Website...")

    sitemap_urls = parse_sitemap(SITEMAP_URL)

    if not sitemap_urls:
        cache = load_json(RAW_DIR / "all_sitemap_urls_cache.json")

        if isinstance(cache, list):
            sitemap_urls = {
                normalize_url(url)
                for url in cache
                if isinstance(url, str)
            }

    records = load_scraped_records()

    unique_urls = set()
    duplicate_urls = set()

    empty_pages = []
    error_pages = []

    for record in records:

        if not isinstance(record, dict):
            continue

        url = normalize_url(record.get("url", ""))

        if not url:
            continue

        if url in unique_urls:
            duplicate_urls.add(url)
        else:
            unique_urls.add(url)

        text = record.get("text", "").strip()

        if not text:
            empty_pages.append(url)

        if text.startswith("[HTTP") or text.startswith("[Error"):
            error_pages.append(url)

    missing_urls = sorted(sitemap_urls - unique_urls)

    coverage = percentage(
        len(unique_urls & sitemap_urls),
        len(sitemap_urls)
    )

    print(f"Live Sitemap URLs : {len(sitemap_urls)}")
    print(f"Scraped URLs      : {len(unique_urls)}")
    print(f"Coverage          : {coverage}%")
    print(f"Missing URLs      : {len(missing_urls)}")
    print(f"Duplicate URLs    : {len(duplicate_urls)}")
    print(f"Empty Pages       : {len(empty_pages)}")
    print(f"Error Pages       : {len(error_pages)}")

    return {
        "coverage": coverage,
        "live_urls": len(sitemap_urls),
        "scraped_urls": len(unique_urls),
        "missing_urls": len(missing_urls),
        "duplicate_urls": len(duplicate_urls),
        "empty_pages": len(empty_pages),
        "error_pages": len(error_pages),
        "missing_url_list": missing_urls,
        "duplicate_url_list": sorted(duplicate_urls),
        "empty_page_list": empty_pages,
        "error_page_list": error_pages
    }