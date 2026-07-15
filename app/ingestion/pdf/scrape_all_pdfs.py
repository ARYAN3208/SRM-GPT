"""
Script to download all missing PDFs from pdf_links.json
"""
import os
import json
import time
import sys

# Add paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(app_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, script_dir)

# Import pdf_downloader directly
import pdf_downloader
download_pdf = pdf_downloader.download_pdf

# Import pdf_loader and pdf_parser manually to avoid relative import issues
import importlib.util
spec = importlib.util.spec_from_file_location("pdf_parser", os.path.join(script_dir, "pdf_parser.py"))
pdf_parser_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf_parser_module)
parse_pdf = pdf_parser_module.parse_pdf

PDF_LINKS_FILE = "app/data/raw/pdf_links.json"
DOWNLOAD_FOLDER = "app/data/uploads"
OUTPUT_FILE = "app/data/raw/ktr_pdf_data.json"

def main():
    print("Loading PDF links...")
    with open(PDF_LINKS_FILE, "r", encoding="utf-8") as f:
        pdf_links = json.load(f)
    
    print(f"Total PDFs to download: {len(pdf_links)}")
    
    # Check already downloaded
    already_downloaded = 0
    for link in pdf_links:
        filename = link.split("/")[-1]
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        save_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(save_path):
            already_downloaded += 1
    
    print(f"Already downloaded: {already_downloaded}")
    print(f"Remaining to download: {len(pdf_links) - already_downloaded}")
    
    # Try to load existing progress
    progress_file = "app/data/raw/pdf_download_progress.json"
    completed_urls = set()
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            completed_urls = set(json.load(f))
        print(f"Loaded progress: {len(completed_urls)} URLs marked as completed")
    
    # Download missing PDFs
    downloaded = []
    failed = []
    
    for i, link in enumerate(pdf_links, 1):
        filename = link.split("/")[-1]
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        save_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Skip if already downloaded or marked as completed
        if os.path.exists(save_path):
            print(f"[{i}/{len(pdf_links)}] Already exists: {filename}")
            downloaded.append({
                "url": link,
                "file": filename,
                "path": save_path,
                "status": "downloaded"
            })
            completed_urls.add(link)
            continue
        
        if link in completed_urls:
            print(f"[{i}/{len(pdf_links)}] Skipping (marked completed): {filename}")
            continue
        
        print(f"[{i}/{len(pdf_links)}] Downloading: {link}")
        result = download_pdf(link, DOWNLOAD_FOLDER)
        
        if result:
            downloaded.append({
                "url": link,
                "file": filename,
                "path": result,
                "status": "downloaded"
            })
            completed_urls.add(link)
        else:
            failed.append(link)
            print(f"  FAILED: {link}")
        
        # Save progress every 25 downloads
        if i % 25 == 0:
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(list(completed_urls), f)
            print(f"Progress saved: {len(completed_urls)} completed")
        
        # Small delay to avoid overwhelming the server
        if i % 50 == 0:
            print(f"\nProgress: {i}/{len(pdf_links)}")
            time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"Download Summary:")
    print(f"  Total: {len(pdf_links)}")
    print(f"  Downloaded: {len(downloaded)}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed URLs ({len(failed)}):")
        for url in failed:
            print(f"  - {url}")
    
    # Parse all downloaded PDFs
    print(f"\n{'='*80}")
    print("Parsing downloaded PDFs...")
    
    parsed_data = []
    for item in downloaded:
        if item["status"] == "downloaded":
            pdf_path = item["path"]
            print(f"Parsing: {item['file']}")
            try:
                pages = parse_pdf(pdf_path)
                parsed_data.append({
                    "url": item["url"],
                    "file": item["file"],
                    "pages": pages
                })
            except Exception as e:
                print(f"  ERROR parsing: {e}")
    
    # Save parsed PDF data
    parsed_output = "app/data/raw/ktr_pdf_data.json"
    with open(parsed_output, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nParsed {len(parsed_data)} PDFs successfully")
    print(f"Saved to: {parsed_output}")

if __name__ == "__main__":
    main()