import requests
import json
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

MISSING_OUT = RAW_DIR / "missing_urls_scraped.json"
SITEMAP_URL = "https://www.srmist.edu.in/sitemap.xml"


def get_all_urls_from_sitemap(sitemap_url):
    """Extract all URLs from sitemap.xml"""
    try:
        response = requests.get(sitemap_url, timeout=10)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        urls = []
        for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            urls.append(url.text)
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []


def get_existing_urls():
    """Get all URLs from existing JSON files"""
    existing = set()
    
    for json_file in RAW_DIR.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for record in data:
                    if isinstance(record, dict) and record.get('url'):
                        existing.add(record['url'])
        except:
            pass
    
    return existing


def scrape_url(url):
    """Scrape single URL - GET EVERYTHING, even empty content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            text = " ".join(text.split())
            
            # ✅ ACCEPT ALL - even if empty or 0 words
            return {
                'url': url,
                'text': text if text else "[Empty page - no content]",
                'title': soup.title.string if soup.title else '',
                'file': ''
            }
        else:
            # Still add even if error status
            return {
                'url': url,
                'text': f"[HTTP {response.status_code} - Could not scrape]",
                'title': '',
                'file': ''
            }
    except Exception as e:
        # Add even if network error
        return {
            'url': url,
            'text': f"[Error: {str(e)}]",
            'title': '',
            'file': ''
        }


def main():
    print("=" * 70)
    print("SCRAPING ALL MISSING URLS (INCLUDING EMPTY PAGES)")
    print("=" * 70)
    
    # Get all sitemap URLs
    print("\n📡 Fetching sitemap.xml...")
    sitemap_urls = get_all_urls_from_sitemap(SITEMAP_URL)
    print(f"✅ Sitemap has: {len(sitemap_urls)} URLs")
    
    # Get existing URLs
    print("\n📊 Checking existing data...")
    existing_urls = get_existing_urls()
    print(f"✅ Already have: {len(existing_urls)} URLs")
    
    # Find missing
    missing_urls = [url for url in sitemap_urls if url not in existing_urls]
    print(f"❌ Missing: {len(missing_urls)} URLs")
    
    if not missing_urls:
        print("\n✅ All URLs already have data!")
        return
    
    # Scrape ALL missing URLs
    print(f"\n" + "=" * 70)
    print(f"🕷️  SCRAPING {len(missing_urls)} MISSING URLS...")
    print("=" * 70)
    
    scraped_data = []
    
    for i, url in enumerate(missing_urls, 1):
        print(f"[{i}/{len(missing_urls)}] {url[:70]}")
        
        result = scrape_url(url)
        # ✅ ADD ALL - no filtering
        if result:
            scraped_data.append(result)
        
        # Rate limit
        time.sleep(1)
    
    # Save ALL missing URLs data
    if scraped_data:
        with open(MISSING_OUT, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS!")
        print("=" * 70)
        print(f"📊 Total scraped: {len(scraped_data)} URLs")
        print(f"💾 Saved to: {MISSING_OUT}")
        print("=" * 70)


if __name__ == "__main__":
    main()