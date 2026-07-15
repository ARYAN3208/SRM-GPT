from pathlib import Path
import json
from collections import Counter

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  Install pdfplumber: pip install pdfplumber")

BASE_DIR = Path(__file__).resolve().parent

RAW_DIR = BASE_DIR / "raw"
UPLOADS_DIR = BASE_DIR / "uploads"
FINAL_DIR = BASE_DIR / "final"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUT = FINAL_DIR / "rag_data.json"


def load_json(path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber"""
    if not PDF_SUPPORT:
        return ""
    
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                text += "\n\n"
        return text
    except Exception as e:
        return ""


def extract_text(item):
    if "pages" in item:
        texts = [page.get("text", "") for page in item["pages"]]
        return "\n\n".join(filter(None, texts))
    return item.get("text") or item.get("content") or ""


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\x00", " ")
    return " ".join(text.split()).strip()


def normalize_records(records, source_name):
    normalized = []
    
    for item in records:
        if not isinstance(item, dict):
            continue
        
        text = clean_text(extract_text(item))
        
        normalized.append({
            "text": text if text else "[No text content]",
            "source": source_name,
            "file_name": item.get("file", ""),
            "url": item.get("url", ""),
            "title": item.get("title", "")
        })
    
    print(f"{source_name}: {len(normalized)} records")
    return normalized


def deduplicate_by_url(docs):
    """Remove duplicate records by URL or file_name"""
    seen = {}
    unique = []
    duplicates = 0
    
    for doc in docs:
        url = doc.get("url", "").strip()
        file_name = doc.get("file_name", "").strip()
        
        # Use URL as primary key, file_name as fallback
        key = url if url else file_name
        
        if key:
            if key not in seen:
                seen[key] = True
                unique.append(doc)
            else:
                duplicates += 1
        else:
            # Keep docs with no identifier
            unique.append(doc)
    
    return unique, duplicates


def chunk_text(text, chunk_size=800, overlap=150):
    if not text or len(text) < 10:
        return [text] if text else [""]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    
    return chunks


def main():
    all_docs = []
    
    # ✅ Load ALL JSON files from raw/
    if RAW_DIR.exists():
        print("=" * 60)
        print("Loading from RAW folder:")
        print("=" * 60)
        json_files = list(RAW_DIR.glob("*.json"))
        print(f"Found {len(json_files)} JSON files\n")
        
        for json_file in sorted(json_files):
            data = load_json(json_file)
            source_name = json_file.stem.replace("_data", "").replace("_", " ")
            docs = normalize_records(data, source_name)
            all_docs.extend(docs)
    
    # ✅ Load ALL JSON files from uploads/
    if UPLOADS_DIR.exists():
        print("\n" + "=" * 60)
        print("Loading JSON from UPLOADS folder:")
        print("=" * 60)
        json_files = list(UPLOADS_DIR.glob("*.json"))
        if json_files:
            print(f"Found {len(json_files)} JSON files\n")
            for json_file in sorted(json_files):
                data = load_json(json_file)
                source_name = f"uploads/{json_file.stem}"
                docs = normalize_records(data, source_name)
                all_docs.extend(docs)
        else:
            print("No JSON files found in uploads\n")
    
    # ✅ Extract ALL PDF files from uploads/
    if UPLOADS_DIR.exists() and PDF_SUPPORT:
        print("\n" + "=" * 60)
        print("Extracting PDF from UPLOADS folder:")
        print("=" * 60)
        pdf_files = list(UPLOADS_DIR.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files\n")
        
        pdf_count = 0
        for pdf_file in sorted(pdf_files):
            try:
                print(f"Processing: {pdf_file.name}")
                text = extract_text_from_pdf(pdf_file)
                text = clean_text(text)
                
                all_docs.append({
                    "text": text if text else "[PDF extracted but empty]",
                    "source": "uploads/pdf",
                    "file_name": pdf_file.name,
                    "url": "",
                    "title": pdf_file.stem
                })
                pdf_count += 1
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {e}")
        
        print(f"\nuploads/pdf: {pdf_count} PDFs extracted")
    
    print("\n" + "=" * 60)
    print(f"TOTAL DOCUMENTS (before dedup): {len(all_docs)}")
    print("=" * 60)
    print(Counter(x["source"] for x in all_docs))
    
    # ✅ DEDUPLICATE by URL
    print("\n" + "=" * 60)
    print("Deduplicating by URL...")
    print("=" * 60)
    all_docs, duplicates_removed = deduplicate_by_url(all_docs)
    print(f"Removed duplicates: {duplicates_removed}")
    print(f"Unique documents: {len(all_docs)}")
    print("=" * 60)
    print(Counter(x["source"] for x in all_docs))
    
    # ✅ Chunk the text
    print("\n" + "=" * 60)
    print("Chunking documents...")
    print("=" * 60)
    chunked = []
    for doc_index, doc in enumerate(all_docs):
        chunks = chunk_text(doc["text"])
        for chunk_index, chunk in enumerate(chunks, start=1):
            chunked.append({
                "chunk_id": f"{doc['source']}-{doc_index}-{chunk_index}",
                "text": chunk,
                "source": doc["source"],
                "file_name": doc["file_name"],
                "url": doc["url"],
                "title": doc.get("title", "")
            })
    
    # ✅ Save to JSON
    with open(FINAL_OUT, "w", encoding="utf-8") as f:
        json.dump(chunked, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS!")
    print("=" * 60)
    print(f"📊 Total unique documents: {len(all_docs)}")
    print(f"📊 Total chunks: {len(chunked)}")
    print(f"💾 Saved to: {FINAL_OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()