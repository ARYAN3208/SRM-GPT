import json
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

KTR_FILE = RAW_DIR / "ktr_website_data.json"
NEW_FILE = RAW_DIR / "new_scraped_data.json"
CACHE_FILE = RAW_DIR / "all_sitemap_urls_cache.json"

SITEMAP_URL = "https://www.srmist.edu.in/sitemap.xml"


def normalize_url(url):
    if not url:
        return ""
    return url.strip().rstrip("/")


def get_all_urls():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            if not data:
                return []
            if isinstance(data[0], dict):
                return [normalize_url(x["url"]) for x in data if x.get("url")]
            return [normalize_url(x) for x in data]

        if isinstance(data, dict):
            if "urls" in data:
                return [normalize_url(x) for x in data["urls"]]
            return [normalize_url(x) for x in data.keys()]

    response = requests.get(SITEMAP_URL, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    urls = []
    for node in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if node.text:
            urls.append(normalize_url(node.text))

    return urls


def load_existing_data():
    records = []

    for file in (KTR_FILE, NEW_FILE):
        if file.exists():
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records.extend(data)

    return records


def get_existing_urls(records):
    existing = set()

    for item in records:
        if not isinstance(item, dict):
            continue

        url = normalize_url(item.get("url", ""))
        text = item.get("text", "").strip()

        if not url or not text:
            continue

        if text.startswith("[HTTP") or text.startswith("[Error"):
            continue

        if text == "[Empty page - no content]":
            continue

        existing.add(url)

    return existing


def scrape_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(class_="entry-content")
            or soup.find(class_="content")
            or soup.body
            or soup
        )

        title = soup.title.get_text(strip=True) if soup.title else ""

        text = main.get_text(" ", strip=True)
        text = " ".join(text.split())

        return {
            "source": "website",
            "url": normalize_url(url),
            "title": title,
            "text": text,
        }

    except Exception as e:
        return {
            "source": "website",
            "url": normalize_url(url),
            "title": "",
            "text": f"[Error: {e}]",
        }


def main():
    print("=" * 70)
    print("SCRAPE REMAINING URLS")
    print("=" * 70)

    sitemap_urls = get_all_urls()
    existing_records = load_existing_data()
    existing_urls = get_existing_urls(existing_records)

    print("Sitemap URLs     :", len(sitemap_urls))
    print("Already Scraped  :", len(existing_urls))

    remaining = [u for u in sitemap_urls if u not in existing_urls]

    print("Remaining URLs   :", len(remaining))

    if not remaining:
        print("Nothing to scrape.")
        return

    new_records = []

    for i, url in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] {url}")
        new_records.append(scrape_url(url))
        time.sleep(1)

    with open(NEW_FILE, "w", encoding="utf-8") as f:
        json.dump(new_records, f, indent=2, ensure_ascii=False)

    print("Saved:", NEW_FILE)


if __name__ == "__main__":
    main()
