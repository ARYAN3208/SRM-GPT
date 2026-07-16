from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
FINAL_DIR = BASE_DIR / "data" / "final"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/137 Safari/537.36"
    )
}


def load_json(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        return response

    except Exception:
        return None


def normalize_url(url):
    if not url:
        return ""

    url = url.strip()

    if url.endswith("/"):
        url = url[:-1]

    return url


def unique_urls(records):
    urls = set()

    for item in records:

        if not isinstance(item, dict):
            continue

        url = normalize_url(item.get("url", ""))

        if url:
            urls.add(url)

    return urls


def parse_sitemap(url):
    response = fetch(url)

    if response is None:
        return set()

    try:
        root = ET.fromstring(response.content)
    except Exception:
        return set()

    urls = set()

    for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):

        if not loc.text:
            continue

        link = loc.text.strip()

        if link.endswith(".xml"):
            urls.update(parse_sitemap(link))
        else:
            urls.add(normalize_url(link))

    return urls


def extract_pdf_links(url):
    response = fetch(url)

    if response is None:
        return set()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")

    pdfs = set()

    for tag in soup.find_all("a", href=True):

        href = urljoin(url, tag["href"])

        if ".pdf" in href.lower():
            pdfs.add(href.split("#")[0])

    return pdfs


def percentage(found, total):
    if total == 0:
        return 0.0

    return round((found / total) * 100, 2)