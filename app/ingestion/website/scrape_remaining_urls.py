"""
Scrape ALL missing URLs from all sitemaps, in PARALLEL for speed.
Saves incrementally every 200 pages - progress is never lost.
Uses a thread pool with per-request retry/backoff for rate limits.
Resumes automatically from scraped_urls_checkpoint.json / new_scraped_data.json.
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

OUTPUT_PATH = Path("new_scraped_data.json")
CHECKPOINT_PATH = Path("scraped_urls_checkpoint.json")
WEB_DATA_PATH = Path("app/data/raw/ktr_website_data.json")
# Cache of every URL discovered from the sitemaps. Once written, the scraper
# can fall back to this if the live sitemap is temporarily blocked (e.g. WAF
# rate-limit), so a single successful fetch is enough to keep working.
URL_CACHE_PATH = Path("all_sitemap_urls_cache.json")

# Number of parallel worker threads. 6 is a safe balance: enough concurrency
# for a large speedup, but low enough to avoid the aggressive 429/403
# rate-limiting that occurred at higher worker counts. The per-request
# retry/backoff in scrape_page still handles occasional limits.
WORKERS = 6

def get_all_sitemap_urls():
    """Get ALL URLs from ALL sitemaps, with retry + disk caching.

    The discovered URL list is cached to URL_CACHE_PATH. If the live sitemap
    is unreachable (e.g. temporary WAF/rate-limit block), the cached list is
    used as a fallback so scraping can still resume.
    """
    # Try the live sitemap with a few retries / backoff.
    all_urls = []
    for attempt in range(5):
        try:
            resp = requests.get("https://www.srmist.edu.in/sitemap.xml", headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"  sitemap.xml -> HTTP {resp.status_code} (attempt {attempt+1}/5)")
                time.sleep(10 * (attempt + 1))
                continue
            soup = BeautifulSoup(resp.text, "xml")
            sitemaps = [s.text.strip() for s in soup.find_all("loc")]
            if not sitemaps:
                print(f"  sitemap.xml returned no <loc> (attempt {attempt+1}/5)")
                time.sleep(10 * (attempt + 1))
                continue

            print(f"Found {len(sitemaps)} sitemaps")
            for sm in sitemaps:
                try:
                    r = requests.get(sm, headers=HEADERS, timeout=30)
                    if r.status_code == 200:
                        s2 = BeautifulSoup(r.text, "xml")
                        urls = [loc.text.strip() for loc in s2.find_all("loc")]
                        all_urls.extend(urls)
                        name = sm.split("/")[-1]
                        print(f"  {name:50} -> {len(urls)} URLs")
                    else:
                        print(f"  {sm.split('/')[-1]:50} -> FAILED ({r.status_code})")
                except Exception as e:
                    print(f"  {sm.split('/')[-1]:50} -> ERROR: {e}")
            break
        except Exception as e:
            print(f"  sitemap fetch error (attempt {attempt+1}/5): {e}")
            time.sleep(10 * (attempt + 1))

    if all_urls:
        # Cache the full discovered list for future (possibly blocked) runs.
        with open(URL_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(set(all_urls)), f, indent=2)
        print(f"Cached {len(set(all_urls))} sitemap URLs to {URL_CACHE_PATH}")
        return list(set(all_urls))

    # Fallback: use the cached URL list if the live fetch failed.
    if URL_CACHE_PATH.exists():
        with open(URL_CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        print(f"Live sitemap unreachable - using cached URL list ({len(cached)} URLs)")
        return list(set(cached))

    print("ERROR: could not fetch sitemaps and no URL cache exists.")
    return []

def extract_text(soup, url):
    """Extract clean text matching existing data format."""
    for tag in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript"]):
        tag.decompose()

    main_content = soup.find("main")
    if main_content:
        text = main_content.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)

    text = " ".join(text.split())
    if not text.strip():
        return None

    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    return {
        "source": "website",
        "url": url,
        "title": title,
        "text": text
    }

def is_blocked_response(text, status_code=None, headers=None):
    """True if the response is the AWS WAF 'Human Verification' / 403 block
    interstitial rather than real page content.

    The SRM WAF (awselb) returns a 405 (not 403) with a 'Human Verification'
    body for blocked requests, so we must detect both the status code AND the
    interstitial content/headers, not just the literal "403 Forbidden" string.
    """
    low = (text or "").lower()
    if "human verification" in low:
        return True
    if "403 forbidden" in low:
        return True
    if status_code in (401, 403, 405, 429):
        # 405 here is the WAF block, not a real "method not allowed".
        return True
    if headers and "awselb" in str(headers.get("Server", "")).lower():
        return True
    return False


def scrape_page(url):
    """Scrape a single page with retry and backoff."""
    for attempt in range(3):
        try:
            # Fresh headers each request to avoid rate limit
            h = HEADERS.copy()
            h["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

            response = requests.get(url, headers=h, timeout=30)

            if response.status_code == 429 or response.status_code == 403:
                wait = 5 * (attempt + 1)
                time.sleep(wait)
                continue

            if response.status_code == 404:
                return {"url": url, "status": "404", "data": None}

            if response.status_code != 200:
                # The SRM WAF often answers blocked GETs with HTTP 405 +
                # a "Human Verification" body (server: awselb). Treat that as a
                # block so the URL is retried later instead of being reported
                # as a hard failure / wrongly marked done.
                if is_blocked_response(response.text, response.status_code, response.headers):
                    return {"url": url, "status": "blocked", "data": None}
                return {"url": url, "status": f"error_{response.status_code}", "data": None}

            # Detect the AWS WAF challenge page BEFORE treating as "empty".
            # A blocked page yields no <main> text, so extract_text() would
            # return None and the URL would wrongly be marked permanently done.
            if is_blocked_response(response.text, response.status_code, response.headers):
                return {"url": url, "status": "blocked", "data": None}

            soup = BeautifulSoup(response.text, "lxml")
            data = extract_text(soup, url)

            if data is None:
                return {"url": url, "status": "empty", "data": None}

            return {"url": url, "status": "ok", "data": data}

        except Exception:
            if attempt < 2:
                time.sleep(2)
                continue
            return {"url": url, "status": "exception", "data": None}

    return {"url": url, "status": "failed_after_retries", "data": None}

def save_progress(scraped, checkpoint_urls):
    """Save scraped data and checkpoint incrementally."""
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scraped, f, indent=2, ensure_ascii=False)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(checkpoint_urls), f, indent=2)

def main():
    print("=" * 60)
    print("LOADING ALL SITEMAP URLS")
    print("=" * 60)
    all_urls = get_all_sitemap_urls()
    all_urls_set = set(u.rstrip("/") for u in all_urls)
    print(f"\nTotal unique URLs from all sitemaps: {len(all_urls_set)}")

    if not all_urls_set:
        print("No URLs available (sitemap blocked and no cache). Cannot scrape. Exiting.")
        return

    # Load existing state
    existing_urls = set()
    scraped_data = []

    if WEB_DATA_PATH.exists():
        with open(WEB_DATA_PATH, "r", encoding="utf-8") as f:
            existing_web = json.load(f)
        for item in existing_web:
            url = item.get("url", "").rstrip("/")
            if url:
                existing_urls.add(url)
        print(f"Existing from ktr_website_data.json: {len(existing_web)}")

    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            existing_urls.update(json.load(f))

    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            scraped_data = loaded
            # Also mark these URLs as already processed so we don't re-scrape
            for item in loaded:
                url = item.get("url", "").rstrip("/")
                if url:
                    existing_urls.add(url)
        print(f"Already in output file: {len(scraped_data)}")

    missing_urls = all_urls_set - existing_urls
    print(f"\nMissing URLs to scrape: {len(missing_urls)}")

    if not missing_urls:
        print("Nothing to scrape. Exiting.")
        return

    print(f"\nScraping with {WORKERS} parallel workers...")

    # ---- Early WAF ban guard -------------------------------------------------
    # If the live site is currently IP-banned (AWS WAF "Human Verification"),
    # a full parallel run would waste every URL as "failed" and the ban would
    # simply be re-hit on the next resume. Probe the base URL first and abort
    # cleanly (without touching the existing output/checkpoint) so the user can
    # retry later or switch to the Wayback/Selenium scraper.
    try:
        probe = requests.get("https://www.srmist.edu.in/", headers=HEADERS, timeout=30)
        if probe.status_code != 200 or is_blocked_response(probe.text, probe.status_code, probe.headers):
            print("\n!!! LIVE SITE CURRENTLY WAF-BANNED (probe returned "
                  f"{probe.status_code}, blocked={is_blocked_response(probe.text, probe.status_code, probe.headers)}).")
            print("    Aborting to avoid wasting the run. Existing output/"
                  "checkpoint are untouched.")
            print("    Retry later, or run scrape_wayback.py / "
                  "scrape_remaining_selenium.py instead.")
            return
    except Exception as e:
        print(f"\n!!! Could not reach live site for ban-check ({e}). Aborting.")
        return

    newly_scraped = 0
    failed = 0
    skipped = 0
    lock = Lock()

    # Track how many URLs have been attempted for progress reporting
    total = len(missing_urls)
    done_counter = 0

    # Circuit breaker: if we see this many consecutive blocked/failed results
    # with zero successes, the IP is likely banned again mid-run -> pause and
    # retry the challenge window, then resume.
    CONSECUTIVE_FAIL_LIMIT = 50
    consecutive_fails = 0

    missing_list = sorted(list(missing_urls))

    def handle_result(result):
        nonlocal newly_scraped, failed, skipped, done_counter, consecutive_fails
        with lock:
            if result["status"] == "ok":
                scraped_data.append(result["data"])
                newly_scraped += 1
                consecutive_fails = 0
                # Successfully scraped -> mark as done so we never re-scrape.
                existing_urls.add(result["url"].rstrip("/"))
            elif result["status"] == "404" or result["status"] == "empty":
                skipped += 1
                consecutive_fails = 0
                # Terminal states (page gone / no text) -> mark done, no retry.
                existing_urls.add(result["url"].rstrip("/"))
            elif result["status"] == "blocked":
                failed += 1
                consecutive_fails += 1
                # WAF-blocked -> DO NOT mark done. Stays "missing" and is
                # retried by the Selenium scraper on the next run.
                pass
            else:
                failed += 1
                consecutive_fails += 1
                # Failed / rate-limited / exception -> DO NOT mark as done.
                # These URLs stay "missing" and are retried on the next
                # run (resume from checkpoint), so no data is silently lost.
                pass
            done_counter += 1

            # Save checkpoint every 200 new pages
            if newly_scraped > 0 and newly_scraped % 200 == 0:
                save_progress(scraped_data, existing_urls)
                print(f"  CHECKPOINT: [{done_counter}/{total}] {newly_scraped} scraped, {skipped} 404, {failed} failed")

            # Progress every 500 processed
            if done_counter % 500 == 0:
                print(f"  PROGRESS: [{done_counter}/{total}] {newly_scraped} scraped, {skipped} 404, {failed} failed")

            # Circuit breaker: prolonged total failure => ban resumed.
            if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT and newly_scraped == 0:
                print(f"\n  !! {consecutive_fails} consecutive failures with 0 "
                      "successes - live site appears WAF-banned again.")
                print("     Stopping early to preserve state. Re-run later or "
                      "use the Wayback/Selenium scraper.")
                # Signal the outer loop to stop by raising inside the lock.
                raise StopIteration

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {executor.submit(scrape_page, url): url for url in missing_list}
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    result = {"url": futures[future], "status": "exception", "data": None}
                try:
                    handle_result(result)
                except StopIteration:
                    # Circuit breaker tripped: cancel remaining work.
                    for f in futures:
                        f.cancel()
                    break
    except StopIteration:
        pass

    save_progress(scraped_data, existing_urls)

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"  Total missing URLs:    {total}")
    print(f"  Successfully scraped:  {newly_scraped}")
    print(f"  404/empty (skipped):   {skipped}")
    print(f"  Failed:                {failed}")
    print(f"  Total in output file:  {len(scraped_data)}")
    print(f"  Saved to:              {OUTPUT_PATH}")

if __name__ == "__main__":
    main()