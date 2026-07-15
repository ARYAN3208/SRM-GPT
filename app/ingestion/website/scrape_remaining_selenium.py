"""
Single-session Selenium scraper for the REMAINING 3512 sitemap URLs that the
requests-based scraper could not fetch because the SRM site sits behind an
AWS WAF (aws-waf-token JS/cookie challenge). Plain `requests` always receives
the "Human Verification" interstitial (or a 403), so it never extracts content.

Why a SINGLE browser session (not one-driver-per-worker):
  - The WAF issues an `aws-waf-token` cookie after its JS challenge runs.
  - That cookie is valid for the whole session and can be reused for
    subsequent page loads. Spinning up many drivers / hammering the site just
    triggers a hard 403 IP ban (observed during testing).
  - We solve the challenge ONCE, then crawl slowly (randomized delays) reusing
    the same cookie. If a 403 appears we pause and re-solve the challenge.

Resume logic:
  - "done" = sitemap URLs already present in ktr_website_data.json +
    scraped_urls_checkpoint.json + new_scraped_data.json.
  - Remaining = all_sitemap_urls_cache.json - done.
  - Successful pages are appended to new_scraped_data.json AND the checkpoint
    (so the requests pipeline can merge them later).
  - Failed URLs are NOT marked done -> retried on the next run.
"""

import json
import time
import random
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

ALL_SITEMAP_PATH = Path("all_sitemap_urls_cache.json")
WEB_DATA_PATH = Path("app/data/raw/ktr_website_data.json")
CHECKPOINT_PATH = Path("scraped_urls_checkpoint.json")
OUTPUT_PATH = Path("new_scraped_data.json")

BASE = "https://www.srmist.edu.in"
MIN_DELAY = 2.0
MAX_DELAY = 5.0
CHALLENGE_WAIT = 7.0       # seconds to let the WAF JS set the cookie
BAN_PAUSE = 120.0          # seconds to wait if we get a 403 ban
RETRY_CHALLENGE = 3

# ---- Proxy support -------------------------------------------------------
# The live SRM site WAF IP-bans this machine. To scrape, run from a
# different egress IP. Easiest: turn on a VPN, then run this script.
# Alternatively, supply proxies (rotates on ban):
#   export SRM_PROXY="http://user:pass@1.2.3.4:8080"
#   export SRM_PROXY_FILE="proxies.txt"   (one proxy per line)
# A single proxy = the VPN egress; a file = rotate through many.
def load_proxies():
    proxies = []
    if os.getenv("SRM_PROXY"):
        proxies.append(os.getenv("SRM_PROXY").strip())
    pf = os.getenv("SRM_PROXY_FILE")
    if pf and Path(pf).exists():
        for line in open(pf, "r", encoding="utf-8"):
            line = line.strip()
            if line:
                proxies.append(line)
    return proxies

PROXIES = load_proxies()


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


def make_driver(proxy=None):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    if proxy:
        # Chrome expects no scheme prefix for --proxy-server
        p = proxy.replace("http://", "").replace("https://", "")
        opts.add_argument(f"--proxy-server={p}")
    return webdriver.Chrome(options=opts)


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


def is_blocked(src, cookies=None):
    """Return True if the page is a WAF challenge / block page rather than
    real content. Block pages are tiny, contain no <main>, and never have the
    aws-waf-token cookie set. Without this robust check, a silently-blocked
    page produces no <main> text, extract_text() returns None, and the URL
    gets marked 'done' forever (poisoning the checkpoint)."""
    if ("Human Verification" in src) or ("403 Forbidden" in src):
        return True
    # Challenge/interstitial pages are tiny and have no real <main> body.
    if "<main" not in src and len(src) < 2500:
        return True
    # If the WAF token cookie was never issued, the challenge was not solved.
    if cookies is not None and not any(
        c.get("name") == "aws-waf-token" for c in cookies
    ):
        return True
    return False


def solve_challenge(driver):
    """Hit the base URL to let the WAF JS run and set aws-waf-token."""
    for _ in range(RETRY_CHALLENGE):
        try:
            driver.get(BASE)
            time.sleep(CHALLENGE_WAIT)
            cookies = {c["name"]: c for c in driver.get_cookies()}
            if "aws-waf-token" in cookies:
                return True
        except Exception:
            time.sleep(5)
    return False


def save_progress(scraped, done_set):
    tmp_o = OUTPUT_PATH.with_suffix(".tmp")
    with open(tmp_o, "w", encoding="utf-8") as f:
        json.dump(scraped, f, indent=2, ensure_ascii=False)
    tmp_o.replace(OUTPUT_PATH)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(done_set), f, indent=2)


def main():
    remaining = get_remaining_urls()
    print(f"Remaining URLs to scrape: {len(remaining)}")
    if not remaining:
        print("Nothing to scrape. Exiting.")
        return

    if PROXIES:
        print(f"Using {len(PROXIES)} proxy/proxies (rotate on ban).")
    else:
        print("No proxy set. If this IP is WAF-banned, turn on a VPN or "
              "set SRM_PROXY / SRM_PROXY_FILE, then re-run.")

    scraped_data = load_json(OUTPUT_PATH, [])
    done_set = set(i.get("url", "").rstrip("/") for i in scraped_data if i.get("url"))
    done_set.update(u.rstrip("/") for u in load_json(CHECKPOINT_PATH, []))

    proxy_idx = 0
    current_proxy = PROXIES[proxy_idx] if PROXIES else None
    driver = make_driver(current_proxy)
    # Solve the WAF challenge once before crawling.
    print("Solving WAF challenge (base URL)...")
    if not solve_challenge(driver):
        print("WARNING: could not obtain aws-waf-token. Will retry per-URL.")
    else:
        print("WAF token obtained.")

    newly = 0
    skipped = 0
    failed = 0
    total = len(remaining)
    last_save = newly

    try:
        for i, url in enumerate(remaining):
            try:
                driver.get(url)
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                src = driver.page_source

                cookies = driver.get_cookies()
                if is_blocked(src, cookies):
                    # Possible ban / expired token -> pause, rotate proxy if
                    # available, re-solve, retry once.
                    print(f"  BLOCKED at [{i+1}/{total}] {url} -> pausing {BAN_PAUSE}s")
                    time.sleep(BAN_PAUSE)
                    if PROXIES and len(PROXIES) > 1:
                        # rotate to next proxy and rebuild the driver
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        proxy_idx = (proxy_idx + 1) % len(PROXIES)
                        current_proxy = PROXIES[proxy_idx]
                        print(f"  Rotating proxy -> {current_proxy}")
                        driver = make_driver(current_proxy)
                    if solve_challenge(driver):
                        driver.get(url)
                        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                        src = driver.page_source
                        cookies = driver.get_cookies()
                    if is_blocked(src, cookies):
                        # Blocked -> DO NOT mark done. Stays 'remaining' and is
                        # retried on the next resume run (no data silently lost).
                        failed += 1
                        continue

                soup = BeautifulSoup(src, "lxml")
                data = extract_text(soup, url)
                if data is None:
                    # Genuine empty page (has <main> but no text) -> skip
                    # permanently. Blocked pages are already caught above.
                    skipped += 1
                    done_set.add(url.rstrip("/"))
                else:
                    scraped_data.append(data)
                    done_set.add(url.rstrip("/"))
                    newly += 1
            except Exception as e:
                failed += 1
                print(f"  EXCEPTION [{i+1}/{total}] {url}: {e}")

            if newly - last_save >= 100:
                save_progress(scraped_data, done_set)
                last_save = newly
                print(f"  CHECKPOINT [{i+1}/{total}] scraped={newly} skip={skipped} fail={failed}")

            if (i + 1) % 250 == 0:
                print(f"  PROGRESS [{i+1}/{total}] scraped={newly} skip={skipped} fail={failed}")
    finally:
        save_progress(scraped_data, done_set)
        try:
            driver.quit()
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("SELENIUM SCRAPE COMPLETE")
    print("=" * 60)
    print(f"  Total remaining:   {total}")
    print(f"  Scraped ok:        {newly}")
    print(f"  Skipped (empty):   {skipped}")
    print(f"  Failed:            {failed}")
    print(f"  Output file size:  {len(scraped_data)}")


if __name__ == "__main__":
    main()