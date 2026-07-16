from pathlib import Path
import json
import re
import hashlib
import unicodedata
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
]

def load_json(path):
    if not path.exists():
        print(f"File not found: {path.name}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {path.name}: {e}")
        return []

def extract_text(item):
    if not isinstance(item, dict):
        return ""
    if "pages" in item:
        texts = []
        for page in item.get("pages", []):
            if isinstance(page, dict):
                t = page.get("text", "").strip()
                if t:
                    texts.append(t)
        return "\n\n".join(texts)
    return (item.get("text") or item.get("content") or "").strip()

def clean_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", " ").replace("\ufeff", " ")
    text = re.sub(r"\.{5,}|…{3,}|·{3,}", " ", text)
    text = re.sub(r"[_=-]{5,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def is_garbled(text):
    if len(text) < 20:
        return True
    total = len(text)
    letters = sum(c.isalpha() for c in text)
    printable = sum(c.isprintable() for c in text)
    controls = sum(unicodedata.category(c).startswith("C") for c in text)
    symbols = sum(c in "|~[]{}<>\\^`" for c in text)
    if printable / total < 0.85:
        return True
    if controls / total > 0.05:
        return True
    if symbols / total > 0.15:
        return True
    if letters / total < 0.10:
        return True
    return False

def normalize_records(records, source):
    docs = []
    for item in records:
        if not isinstance(item, dict):
            continue
        text = clean_text(extract_text(item))
        if len(text) < 20:
            continue
        if is_garbled(text):
            continue
        docs.append({
            "text": text,
            "source": source,
            "document_type": "pdf" if "pdf" in source else "website",
            "url": item.get("url","").strip(),
            "file_name": item.get("file","").strip(),
            "title": item.get("title","").strip()
        })
    return docs

def deduplicate_documents(docs):
    unique=[]
    seen_keys=set()
    seen_text=set()
    for d in docs:
        key=d["url"] or d["file_name"]
        th=hashlib.md5(d["text"].encode()).hexdigest()
        if key and key in seen_keys:
            continue
        if th in seen_text:
            continue
        if key:
            seen_keys.add(key)
        seen_text.add(th)
        unique.append(d)
    return unique

def split_sentences(text):
    parts=re.split(r'(?<=[.!?।])\s+|\n+',text)
    return [p.strip() for p in parts if p.strip()]

def chunk_text(text,chunk_size=700,overlap=120):
    sents=split_sentences(text)
    chunks=[]
    current=""
    for s in sents:
        if not current:
            current=s
            continue
        if len(current)+len(s)+1<=chunk_size:
            current+=" "+s
        else:
            chunks.append(current)
            words=current.split()
            ov=""
            while words and len(ov)<overlap:
                ov=(words.pop()+" "+ov).strip()
            current=(ov+" "+s).strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c)>=30]

def create_chunks(docs):
    out=[]
    seen=set()
    for doc in docs:
        pieces=chunk_text(doc["text"])
        total=len(pieces)
        for i,p in enumerate(pieces,1):
            h=hashlib.md5((doc["source"]+doc["url"]+doc["file_name"]+p).encode()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            out.append({
                "chunk_id":h,
                "text":p,
                "source":doc["source"],
                "document_type":doc["document_type"],
                "file_name":doc["file_name"],
                "url":doc["url"],
                "title":doc["title"],
                "chunk_number":i,
                "total_chunks":total,
                "chunk_length":len(p)
            })
    return out

def main():
    docs=[]
    for filename in TARGET_FILES:
        data=load_json(RAW_DIR/filename)
        if not data:
            continue
        source=filename.replace("_data.json","").replace(".json","").replace("_"," ")
        docs.extend(normalize_records(data,source))
    docs=deduplicate_documents(docs)
    chunks=create_chunks(docs)
    with open(FINAL_OUT,"w",encoding="utf-8") as f:
        json.dump(chunks,f,indent=2,ensure_ascii=False)
    print(f"Documents: {len(docs)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Saved: {FINAL_OUT}")

if __name__=="__main__":
    main()
