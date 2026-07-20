import json
import os
import time
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup

# Subdomains provided by the user
SUBDOMAINS = [
    "emanager.srmist.edu.in",
    "srmadmtest2023.srmist.edu.in",
    "www.distanceeducation.srmist.edu.in",
    "academia.srmist.edu.in",
    "webstor.srmist.edu.in",
    "journal.srmist.edu.in",
    "f5tata3dns.srmist.edu.in",
    "phdee.srmist.edu.in",
    "siddha.srmist.edu.in",
    "srmadmtest2021.srmist.edu.in",
    "srv01.srmist.edu.in",
    "care.srmist.edu.in",
    "linkproof3.srmist.edu.in",
    "shbf.srmist.edu.in",
    "uatserver.srmist.edu.in",
    "iqac.srmist.edu.in",
    "mdashboard.srmist.edu.in",
    "evarsity.srmist.edu.in",
    "urp.srmist.edu.in",
    "srmjee2022.srmist.edu.in",
    "devphp.srmist.edu.in",
    "itkmservicedesk.srmist.edu.in",
    "radius.srmist.edu.in",
    "medicalresearch.srmist.edu.in",
    "transport.srmist.edu.in",
    "answerkey.srmist.edu.in",
    "grievances.srmist.edu.in",
    "pbi2prod.srmist.edu.in",
    "urppg.srmist.edu.in",
    "rmiliss2024.srmist.edu.in",
    "www.srmist.edu.in",
    "ecapp.srmist.edu.in",
    "ssp.srmist.edu.in",
    "files.srmist.edu.in",
    "stgurpweb.srmist.edu.in",
    "applications.srmist.edu.in",
    "distanceeducation.srmist.edu.in",
    "ilms.srmist.edu.in",
    "moocsplus.srmist.edu.in",
    "newsitepreview.srmist.edu.in",
    "admissions.srmist.edu.in",
    "argocd.srmist.edu.in",
    "gp.srmist.edu.in",
    "iach.srmist.edu.in",
    "wildcard.srmist.edu.in",
    "www.srmadmtest2021.srmist.edu.in",
    "curiousbees.srmist.edu.in",
    "sp.srmist.edu.in",
    "rd.srmist.edu.in",
    "f5airtel1dns.srmist.edu.in",
    "iac.srmist.edu.in",
    "lcm.srmist.edu.in",
    "msladmissions.srmist.edu.in",
    "bit.srmist.edu.in",
    "alumni.srmist.edu.in",
    "delivery.srmist.edu.in",
    "teamdeck.srmist.edu.in",
    "urpauth.srmist.edu.in",
    "www.applications.srmist.edu.in",
    "www.srmjee2022.srmist.edu.in",
    "c19.srmist.edu.in",
    "medical.srmist.edu.in",
    "urpapp.srmist.edu.in",
    "ejournal.srmist.edu.in",
    "devevarsity.srmist.edu.in",
    "dspace.srmist.edu.in",
    "hostellogin.srmist.edu.in",
    "admission.srmist.edu.in",
    "library.srmist.edu.in",
    "api.curiousbees.srmist.edu.in",
    "mail.srmist.edu.in",
    "srmadmtest2020.srmist.edu.in",
    "career.srmist.edu.in",
    "devwebsite.srmist.edu.in",
    "iris.srmist.edu.in",
    "counseling.srmist.edu.in",
    "www1.srmist.edu.in",
    "linkproof4.srmist.edu.in",
    "uatwebsite.srmist.edu.in",
    "uba.srmist.edu.in",
    "www.iris.srmist.edu.in",
    "ddesss.srmist.edu.in",
    "ecounseling.srmist.edu.in",
    "evarsity1.srmist.edu.in",
    "feekart.srmist.edu.in",
    "devweb.srmist.edu.in",
    "examcell.srmist.edu.in",
    "careers.srmist.edu.in",
    "access.srmist.edu.in",
    "hostel.srmist.edu.in",
    "sd.srmist.edu.in",
    "srmjee.srmist.edu.in",
    "www.srmadmtest2023.srmist.edu.in",
    "lms.srmist.edu.in",
    "cctr.srmist.edu.in",
    "cdcepro.srmist.edu.in",
    "ecampus.srmist.edu.in",
    "uropmfp.srmist.edu.in",
    "urpuat.srmist.edu.in",
    "dental.srmist.edu.in",
    "intlapplications.srmist.edu.in",
    "opac.srmist.edu.in",
    "skillnest.srmist.edu.in",
    "sms.srmist.edu.in",
    "stgwebsite.srmist.edu.in",
    "srmiliss2024.srmist.edu.in",
    "scheduulr.srmist.edu.in",
    "students-counseling.srmist.edu.in",
    "apps.srmist.edu.in",
    "ctechsp.srmist.edu.in",
    "dld.srmist.edu.in",
    "empower.srmist.edu.in",
    "www.radius.srmist.edu.in",
    "hpcw1.srmist.edu.in"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

MAX_DEPTH = 5
MAX_PAGES_PER_SUBDOMAIN = 999999
TIMEOUT = 10
OUTPUT_FILE = "app/data/raw/subdomains_scraped_data.json"

results = []
results_lock = Lock()
visited_urls = set()
visited_lock = Lock()

def clean_text(soup):
    for tag in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    text = main.get_text(separator=" ", strip=True) if main else soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    if parsed.netloc != base_domain:
        return False
    # Avoid static assets
    path = parsed.path.lower()
    for ext in [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".css", ".js", ".docx", ".xlsx", ".mp4", ".mp3"]:
        if path.endswith(ext):
            return False
    return True

def crawl_subdomain(subdomain):
    base_url = f"https://{subdomain}"
    base_domain = subdomain
    
    # Try HTTPS first, fallback to HTTP if needed
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    except Exception:
        base_url = f"http://{subdomain}"
        try:
            r = requests.get(base_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        except Exception:
            print(f"[-] Reachability failed for {subdomain}")
            return
            
    print(f"[+] Scraping {subdomain} starting at {base_url}...")
    
    queue = [(base_url, 0)]
    local_visited = set()
    pages_scraped = 0
    
    while queue and pages_scraped < MAX_PAGES_PER_SUBDOMAIN:
        current_url, depth = queue.pop(0)
        
        # Check global visited set
        with visited_lock:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            
        local_visited.add(current_url)
        
        try:
            resp = requests.get(current_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            text = clean_text(soup)
            title = soup.title.string.strip() if soup.title else ""
            
            if text:
                with results_lock:
                    results.append({
                        "source": "website",
                        "url": current_url,
                        "title": title,
                        "text": text
                    })
                pages_scraped += 1
                print(f"    [{pages_scraped}] Scraped: {current_url}")
                
            # Extract links if not at max depth
            if depth < MAX_DEPTH:
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    full_url = urljoin(current_url, href).split("#")[0].rstrip("/")
                    if is_valid_url(full_url, base_domain) and full_url not in local_visited:
                        queue.append((full_url, depth + 1))
                        
        except Exception as e:
            # Silent fallback for scrape errors
            pass

def main():
    print(f"Starting scrape on {len(SUBDOMAINS)} subdomains...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Process subdomains concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(crawl_subdomain, sub): sub for sub in SUBDOMAINS}
        for future in as_completed(futures):
            sub = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[-] Error crawling {sub}: {e}")
                
    # Save the output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n============================================================")
    print(f"SCRAPING COMPLETE. Scraped {len(results)} pages across subdomains.")
    print(f"Saved to {OUTPUT_FILE}")
    print(f"============================================================")

if __name__ == "__main__":
    main()
