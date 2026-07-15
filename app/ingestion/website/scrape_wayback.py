"""
Wayback Machine scraper for the REMAINING sitemap URLs.

WHY THIS EXISTS:
  The live srmist.edu.in sits behind an AWS/Neustar WAF that is
  currently IP-banning this machine (every request returns a "Human
  Verification" challenge, no aws-waf-token cookie is ever issued). A live
  Selenium/requests scrape therefore returns 0 pages.

  web.archive.org (the Internet Archive Wayback Machine) is NOT banned,
  and it holds archived snapshots of essentially all SRM pages. This script
  fetches each remaining URL's *closest archived snapshot* instead of the
  live site, so we can still build the complete knowledge base. Content is
  slightly older than live but perfectly usable for RAG.

RESUME LOGIC (same as the other scrapers):
  "done" = URLs already in ktr_website_data.json + scraped_urls_checkpoint.json
           + new_scraped_data.json.
  Remaining = all_sitemap_urls_cache.json - done.
  Successful pages are appended to new_scraped_data.json AND the checkpoint.
  URLs with no archived snapshot are skipped (marked done) so we don't
  retry them forever.
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

ALL_SITEMAP_PATH = Path("all_sitemap_urls_cache.json")
WEB_DATA_PATH = Path("app/data/raw/ktr_website_data.json")
CHECKPOINT_PATH = Path("scraped_urls_checkpoint.json")
OUTPUT_PATH = Path("new_scraped_data.json")

WAYBACK_AVAIL = "https://archive.org/wayback/available"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
WORKERS = 4
SNAPSHOT_TIMEOUT = 30
AVAIL_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def load_json(path, default=None):
    if not Path(path).exists():
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_remaining_urls():
    all_urls = set(u.rstrip("/") for u in load_json(ALL_SITEMAP_PATH))
    done = set()
    for item in load_json(WEB_DATA_PATH, []):
        u = item.get("url", "")
        if u:
            done.add(u.rstrip("/"))
    done.update(u.rstrip("/") for u in load_json(CHECKPOINT_PATH, []))
    for item in load_json(OUTPUT_PATH, []):
        u = item.get("url", "")
        if u:
            done.add(u.rstrip("/"))
    return sorted(all_urls - done)


def extract_text(soup, url):
    for tag in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript"]):
        tag.decompose()
    main = soup.find("main")
    text = main.get_text(separator=" ", strip=True) if main else soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    if not text.strip():
        return None
    title = soup.title.get_text(strip=True) if soup.title else ""
    return {"source": "website", "url": url, "title": title, "text": text}


def fetch_snapshot(url):
    """Return (status, data) for one URL via the Wayback Machine."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(
                WAYBACK_AVAIL,
                params={"url": url},
                headers=HEADERS,
                timeout=AVAIL_TIMEOUT,
            )
            if r.status_code == 429 or r.status_code >= 500:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                return {"url": url, "status": f"avail_{r.status_code}", "data": None}
            if r.status_code != 200:
                return {"url": url, "status": f"avail_{r.status_code}", "data": None}

            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if not snap.get("available"):
                return {"url": url, "status": "no_snapshot", "data": None}
            snap_url = snap.get("url")
            if not snap_url:
                return {"url": url, "status": "no_snapshot", "data": None}
            if snap_url.startswith("http://"):
                snap_url = snap_url.replace("http://", "https://", 1)

            # Snap url already points at web.archive.org (not banned).
            resp = requests.get(snap_url, headers=HEADERS, timeout=SNAPSHOT_TIMEOUT)
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                return {"url": url, "status": f"snap_{resp.status_code}", "data": None}
            if resp.status_code != 200:
                return {"url": url, "status": f"snap_{resp.status_code}", "data": None}

            soup = BeautifulSoup(resp.text, "lxml")
            data = extract_text(soup, url)
            if data is None:
                return {"url": url, "status": "empty", "data": None}
            data["archive_url"] = snap_url
            return {"url": url, "status": "ok", "data": data}

        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return {"url": url, "status": f"exception:{e}", "data": None}


def save_progress(scraped, checkpoint_urls):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scraped, f, indent=2, ensure_ascii=False)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(checkpoint_urls), f, indent=2)


def main():
    remaining = get_remaining_urls()
    print(f"Remaining URLs to scrape via Wayback: {len(remaining)}")
    if not remaining:
        print("Nothing to scrape. Exiting.")
        return

    scraped_data = load_json(OUTPUT_PATH, [])
    existing_urls = set(
        i.get("url", "").rstrip("/") for i in scraped_data if i.get("url")
    )
    existing_urls.update(u.rstrip("/") for u in load_json(CHECKPOINT_PATH, []))

    newly = 0
    skipped = 0
    failed = 0
    lock = Lock()
    total = len(remaining)
    done_counter = 0

    def handle_result(result):
        nonlocal newly, skipped, failed, done_counter
        with lock:
            if result["status"] == "ok":
                scraped_data.append(result["data"])
                newly += 1
                existing_urls.add(result["url"].rstrip("/"))
            elif result["status"] in ("no_snapshot", "empty"):
                skipped += 1
                existing_urls.add(result["url"].rstrip("/"))  # nothing to get
            else:
                failed += 1
                # Transient failure (timeout/5xx). Leave URL "remaining"
                # so it is retried on the next run.
                pass
            done_counter += 1
            print(f"  [{done_counter}/{total}] URL: {result['url']} -> status: {result['status']}")

            if newly > 0 and newly % 50 == 0:
                save_progress(scraped_data, existing_urls)
                print(f"  CHECKPOINT: [{done_counter}/{total}] "
                      f"{newly} scraped, {skipped} skipped, {failed} failed")
            elif done_counter % 100 == 0:
                print(f"  PROGRESS:  [{done_counter}/{total}] "
                      f"{newly} scraped, {skipped} skipped, {failed} failed")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fetch_snapshot, u): u for u in remaining}
        for future in as_completed(futures):
            try:
                res = future.result()
            except Exception as e:
                res = {"url": futures[future], "status": f"exception:{e}", "data": None}
            handle_result(res)

    save_progress(scraped_data, existing_urls)

    print("\n" + "=" * 60)
    print("WAYBACK SCRAPE COMPLETE")
    print("=" * 60)
    print(f"  Total remaining:     {total}")
    print(f"  Successfully scraped: {newly}")
    print(f"  Skipped (none/arch): {skipped}")
    print(f"  Failed (retry next):  {failed}")
    print(f"  Total in output:      {len(scraped_data)}")
    print(f"  Saved to:             {OUTPUT_PATH}")


if __name__ == "__main__":
    main()