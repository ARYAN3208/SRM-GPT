import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
UPLOADS_DIR = RAW_DIR.parent / "uploads"

SITEMAP = "https://www.srmist.edu.in/sitemap.xml"

WEBSITE_FILES = [
    RAW_DIR / "ktr_website_data.json",
    RAW_DIR / "new_scraped_data.json",
]

PDF_DATA = RAW_DIR / "ktr_pdf_data.json"
RAG_DATA = BASE_DIR / "final" / "rag_data.json"

def load(path):
    if not path.exists():
        return []
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)

def fetch_sitemap(url):
    seen=set()
    urls=set()
    stack=[url]
    while stack:
        sm=stack.pop()
        if sm in seen:
            continue
        seen.add(sm)
        try:
            r=requests.get(sm,timeout=20)
            r.raise_for_status()
            root=ET.fromstring(r.content)
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                if not loc.text:
                    continue
                link=loc.text.strip()
                if link.endswith(".xml"):
                    stack.append(link)
                else:
                    urls.add(link.rstrip("/"))
        except Exception:
            pass
    return urls

def collect_web_urls():
    urls=set()
    records=0
    for f in WEBSITE_FILES:
        data=load(f)
        records+=len(data)
        for item in data:
            if isinstance(item,dict):
                u=item.get("url","").rstrip("/")
                if u:
                    urls.add(u)
    return urls,records

def collect_pdf_links():
    data=load(PDF_DATA)
    links=set()
    for item in data:
        if isinstance(item,dict):
            u=item.get("url","")
            if u:
                links.add(u)
    return links,len(data)

def live_pdf_links(pages):
    pdfs=set()
    s=requests.Session()
    for i,url in enumerate(sorted(pages),1):
        try:
            r=s.get(url,timeout=15)
            if r.status_code!=200:
                continue
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.find_all("a",href=True):
                href=urljoin(url,a["href"])
                if ".pdf" in href.lower():
                    pdfs.add(href.split("#")[0])
        except Exception:
            pass
        if i%100==0:
            print(f"Checked {i}/{len(pages)} pages")
    return pdfs

def main():
    print("="*70)
    print("SRM DATASET VERIFICATION")
    print("="*70)

    sitemap_urls=fetch_sitemap(SITEMAP)
    print(f"Live sitemap URLs : {len(sitemap_urls)}")

    web_urls,web_records=collect_web_urls()
    print(f"Website records   : {web_records}")
    print(f"Unique URLs       : {len(web_urls)}")

    missing=sorted(sitemap_urls-web_urls)
    coverage=(len(web_urls & sitemap_urls)/len(sitemap_urls)*100) if sitemap_urls else 0

    print(f"Website coverage  : {coverage:.2f}%")
    print(f"Missing URLs      : {len(missing)}")

    pdf_links,pdf_records=collect_pdf_links()
    print(f"Parsed PDFs       : {pdf_records}")

    downloaded=0
    if UPLOADS_DIR.exists():
        downloaded=len(list(UPLOADS_DIR.glob("*.pdf")))
    print(f"Downloaded PDFs   : {downloaded}")

    print("\nChecking live PDF links (this can take time)...")
    live_pdfs=live_pdf_links(sitemap_urls)

    pdf_cov=(len(pdf_links & live_pdfs)/len(live_pdfs)*100) if live_pdfs else 0
    print(f"Live PDF links    : {len(live_pdfs)}")
    print(f"PDF coverage      : {pdf_cov:.2f}%")

    rag=load(RAG_DATA)
    print(f"RAG chunks        : {len(rag)}")

    print("\nMissing sitemap URLs:")
    for u in missing[:100]:
        print(u)
    if len(missing)>100:
        print(f"... {len(missing)-100} more")

if __name__=="__main__":
    main()
