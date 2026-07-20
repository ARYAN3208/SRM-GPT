import requests
import json
from pathlib import Path
import time
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
MISSING_OUT = RAW_DIR / "missing_urls_scraped.json"
CACHE_FILE = RAW_DIR / "all_sitemap_urls_cache.json"


def get_all_urls():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        urls = json.load(f)
    return [u.rstrip('/') for u in urls]  # ✅ normalize


def get_existing_urls():
    existing = set()
    for json_file in RAW_DIR.glob("*.json"):
        if json_file.name in ["all_sitemap_urls_cache.json", "missing_urls_scraped.json"]:
            continue
        try:
            data = json.load(open(json_file, 'r', encoding='utf-8'))
            if isinstance(data, list):
                for record in data:
                    if isinstance(record, dict) and record.get('url'):
                        existing.add(record['url'].rstrip('/'))  # ✅ normalize
        except:
            pass
    return existing


def scrape_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = " ".join(soup.get_text(separator=' ', strip=True).split())
            return {
                'url': url,
                'text': text if text else "[Empty page]",
                'title': soup.title.string if soup.title else '',
                'file': ''
            }
        return {
            'url': url,
            'text': f"[HTTP {response.status_code}]",
            'title': '',
            'file': ''
        }
    except Exception as e:
        return {
            'url': url,
            'text': f"[Error: {str(e)[:100]}]",
            'title': '',
            'file': ''
        }


def main():
    print("=" * 60)
    print("Scraping Missing URLs")
    print("=" * 60)

    all_urls = get_all_urls()
    print(f"Total in sitemap cache : {len(all_urls)}")

    existing = get_existing_urls()
    print(f"Already have           : {len(existing)}")

    missing = [url for url in all_urls if url not in existing]
    print(f"Missing                : {len(missing)}")

    if not missing:
        print("✅ All URLs already have data!")
        return

    print(f"\nScraping {len(missing)} URLs...")
    print("=" * 60)

    scraped = []
    success = 0
    failed = 0

    for i, url in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {url[:70]}")
        result = scrape_url(url)
        scraped.append(result)

        if result['text'].startswith("["):
            failed += 1
        else:
            success += 1

        time.sleep(0.5)

    with open(MISSING_OUT, 'w', encoding='utf-8') as f:
        json.dump(scraped, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("✅ Done!")
    print(f"✅ Success : {success}")
    print(f"❌ Failed  : {failed}")
    print(f"💾 Saved to: {MISSING_OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()