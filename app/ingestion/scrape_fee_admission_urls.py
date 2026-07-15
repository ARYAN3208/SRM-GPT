"""
SCRIPTS TO SCRAPE:
==================
1. https://www.srmist.edu.in/admission-india/engineering-technology/
2. https://www.srmist.edu.in/admission-india/engineering-technology/programs-offered/
3. https://www.srmist.edu.in/admission-india/medicine-health-sciences/
4. https://www.srmist.edu.in/admission-india/medicine-health-sciences/programs-offered/
5. https://www.srmist.edu.in/admission-india/management/
6. https://www.srmist.edu.in/admission-india/management/programs-offered/
7. https://www.srmist.edu.in/admission-india/science-humanities/
8. https://www.srmist.edu.in/admission-india/science-humanities/programs-offered/
9. https://www.srmist.edu.in/srmjeee/
10. https://www.srmist.edu.in/srmjeem/
11. https://www.srmist.edu.in/srmjeel/
12. https://www.srmist.edu.in/international-admissions/
13. https://www.srmist.edu.in/fees-and-scholarships/
14. https://www.srmist.edu.in/scholarships/
15. https://www.srmist.edu.in/hostel/
16. https://www.srmist.edu.in/hostel-facilities/
17. https://www.srmist.edu.in/admission-india/engineering-technology/b-tech/
18. https://www.srmist.edu.in/admission-india/engineering-technology/m-tech/
19. https://www.srmist.edu.in/iqac/public-disclosure/
"""

import json
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

TARGET_URLS = [
    "https://www.srmist.edu.in/admission-india/",
    "https://www.srmist.edu.in/admission-india/engineering-technology/",
    "https://www.srmist.edu.in/admission-india/engineering-technology/programs-offered/",
    "https://www.srmist.edu.in/admission-india/medicine-health-sciences/",
    "https://www.srmist.edu.in/admission-india/medicine-health-sciences/programs-offered/",
    "https://www.srmist.edu.in/admission-india/management/",
    "https://www.srmist.edu.in/admission-india/management/programs-offered/",
    "https://www.srmist.edu.in/admission-india/science-humanities/",
    "https://www.srmist.edu.in/admission-india/science-humanities/programs-offered/",
    
    "https://www.srmist.edu.in/srmjeee/",
    "https://www.srmist.edu.in/srmjeem/",
    "https://www.srmist.edu.in/srmjeel/",
    
    "https://www.srmist.edu.in/international-admissions/",
    
    "https://www.srmist.edu.in/fees-and-scholarships/",
    "https://www.srmist.edu.in/scholarships/",
    "https://www.srmist.edu.in/hostel/",
    "https://www.srmist.edu.in/hostel-facilities/",
    
    "https://www.srmist.edu.in/admission-india/engineering-technology/b-tech/",
    "https://www.srmist.edu.in/admission-india/engineering-technology/m-tech/",
    
    "https://www.srmist.edu.in/iqac/public-disclosure/",
    
    "https://www.srmist.edu.in/ugc/",
    
    "https://www.srmist.edu.in/career-centre/",
    "https://www.srmist.edu.in/placements/",
]

def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"  FAILED: {response.status_code} - {url}")
            return None
        soup = BeautifulSoup(response.text, "lxml")
        return soup
    except Exception as e:
        print(f"  ERROR: {e} - {url}")
        return None

def extract_text_from_soup(soup, url):
    """Extract clean text from BeautifulSoup object."""
    if soup is None:
        return None
    
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()
    
    main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup.find("div", class_="entry-content")
    
    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)
    
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) > 2:
            lines.append(line)
    
    return "\n".join(lines)

def main():
    results = []
    
    print(f"Scraping {len(TARGET_URLS)} targeted URLs for fee/admission data...")
    print("=" * 80)
    
    for i, url in enumerate(TARGET_URLS, 1):
        print(f"\n[{i}/{len(TARGET_URLS)}] Scraping: {url}")
        soup = scrape_page(url)
        
        if soup is None:
            print(f"  SKIPPED: Could not scrape {url}")
            continue
        
        text = extract_text_from_soup(soup, url)
        
        if text and len(text) > 200:
            results.append({
                "url": url,
                "text": text,
                "source_type": "website",
                "file_name": url.rstrip("/").split("/")[-1] + ".html"
            })
            print(f"  SUCCESS: {len(text)} chars extracted")
        else:
            print(f"  SKIPPED: Insufficient text ({len(text) if text else 0} chars)")
        
        if i < len(TARGET_URLS):
            time.sleep(1)
    
    output_path = "app/data/raw/fee_admission_targeted_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 80}")
    print(f"Completed! Scraped {len(results)} pages successfully.")
    print(f"Saved to: {output_path}")
    
    print(f"\nSummary:")
    for r in results:
        url = r["url"]
        text_preview = r["text"][:100].replace("\n", " ")
        print(f"  - {url}")
        print(f"    -> {text_preview}...")

if __name__ == "__main__":
    main()