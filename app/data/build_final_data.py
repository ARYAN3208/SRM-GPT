from pathlib import Path
import json
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent

RAW_DIR = BASE_DIR / "raw"
FINAL_DIR = BASE_DIR / "final"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUT = FINAL_DIR / "rag_data.json"


TARGET_FILES = [
    "ktr_pdf_data.json",          
    "ktr_website_data.json",        
    "new_scraped_data.json",    
    "missing_urls_scraped.json",
    "subdomains_scraped_data.json"
    
]


def load_json(path):
    if not path.exists():
        print(f"⚠️  Missing: {path.name}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []


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
    skipped = 0

    for item in records:
        if not isinstance(item, dict):
            skipped += 1
            continue

        text = clean_text(extract_text(item))

        if not text or len(text) < 20:
            skipped += 1
            continue

        normalized.append({
            "text": text,
            "source": source_name,
            "file_name": item.get("file", ""),
            "url": item.get("url", ""),
            "title": item.get("title", "")
        })

    print(f"  {source_name}: {len(normalized)} records ({skipped} skipped)")
    return normalized


def deduplicate_by_url(docs):
    """Remove duplicate records by URL or file_name"""
    seen = {}
    unique = []
    duplicates = 0

    for doc in docs:
        url = doc.get("url", "").strip()
        file_name = doc.get("file_name", "").strip()

        key = url if url else file_name

        if key:
            if key not in seen:
                seen[key] = True
                unique.append(doc)
            else:
                duplicates += 1
        else:
            # No identifier - keep it
            unique.append(doc)

    return unique, duplicates


def chunk_text(text, chunk_size=800, overlap=150):
    if not text or len(text) < 10:
        return [text] if text else []

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

    print("=" * 60)
    print("Loading CLEAN source files from RAW folder:")
    print("=" * 60)

    for filename in TARGET_FILES:
        path = RAW_DIR / filename
        print(f"\n📂 {filename}")

        if not path.exists():
            print(f"  ❌ FILE NOT FOUND - skipping")
            continue

        data = load_json(path)
        source_name = filename.replace("_data.json", "").replace(".json", "").replace("_", " ")
        docs = normalize_records(data, source_name)
        all_docs.extend(docs)

    print("\n" + "=" * 60)
    print(f"TOTAL DOCUMENTS (before dedup): {len(all_docs)}")
    print("=" * 60)
    print(Counter(x["source"] for x in all_docs))

    # Deduplicate by URL
    print("\n" + "=" * 60)
    print("Deduplicating by URL...")
    print("=" * 60)
    all_docs, duplicates_removed = deduplicate_by_url(all_docs)
    print(f"✅ Removed duplicates: {duplicates_removed}")
    print(f"✅ Unique documents: {len(all_docs)}")
    print("=" * 60)
    print(Counter(x["source"] for x in all_docs))

    # Chunk
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

    # Save
    with open(FINAL_OUT, "w", encoding="utf-8") as f:
        json.dump(chunked, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("✅ SUCCESS!")
    print("=" * 60)
    print(f"📊 Total unique documents : {len(all_docs)}")
    print(f"📊 Total chunks           : {len(chunked)}")
    print(f"💾 Saved to               : {FINAL_OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()