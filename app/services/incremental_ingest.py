from pathlib import Path
import hashlib
import time
from typing import List, Dict, Any, Tuple

import chromadb
from sentence_transformers import SentenceTransformer

UPLOAD_DIR = Path("app/data/uploads")
CHROMA_PATH = "app/data/chroma_db"
COLLECTION_NAME = "srm_knowledge_base"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def clean_text(t: str) -> str:
    t = t.replace("\x00", " ")
    t = " ".join(t.split())
    return t.strip()

def chunk_text(text: str, chunk_size: int = 1400, overlap: int = 250) -> List[str]:
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(i + chunk_size, n)
        chunks.append(text[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks

def extract_text_from_pdf(path: Path) -> List[Tuple[int, str]]:
    try:
        import pdfplumber
        out = []
        with pdfplumber.open(str(path)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                out.append((idx, page.extract_text() or ""))
        return out
    except Exception:
        from pypdf import PdfReader
        r = PdfReader(str(path))
        return [(i, (p.extract_text() or "")) for i, p in enumerate(r.pages, start=1)]

def extract_text_from_image(path: Path) -> str:
    from PIL import Image
    import pytesseract
    img = Image.open(str(path)).convert("RGB")
    return pytesseract.image_to_string(img)

def _chunk_id(file_id: str, page: int, chunk_index: int, text: str) -> str:
    base = f"{file_id}|{page}|{chunk_index}|{text}"
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()

def index_one_file(path: Path, campus: str = "ktr", category: str = "general") -> Dict[str, Any]:
    """
    Extract -> chunk -> embed -> upsert into Chroma.
    """
    suffix = path.suffix.lower()
    file_hash = sha256_file(path)
    file_id = hashlib.sha1(str(path.resolve()).encode("utf-8", errors="ignore")).hexdigest()

    try:
        collection.delete(where={"file_id": file_id})
    except Exception:
        pass

    docs: List[str] = []
    metas: List[dict] = []
    ids: List[str] = []

    if suffix == ".pdf":
        source = "pdf"
        pages = extract_text_from_pdf(path)
        for page_num, page_text in pages:
            page_text = clean_text(page_text)
            for ci, ch in enumerate(chunk_text(page_text), start=1):
                ch = ch.strip()
                if not ch:
                    continue
                docs.append(ch)
                metas.append({
                    "source": "pdf",
                    "campus": campus,
                    "category": category,
                    "file_name": path.name,
                    "file_id": file_id,
                    "page": page_num,
                    "chunk_index": ci,
                    "hash": file_hash,
                })
                ids.append(_chunk_id(file_id, page_num, ci, ch))

    elif suffix in [".png", ".jpg", ".jpeg"]:
        source = "ocr"
        text = clean_text(extract_text_from_image(path))
        for ci, ch in enumerate(chunk_text(text), start=1):
            ch = ch.strip()
            if not ch:
                continue
            docs.append(ch)
            metas.append({
                "source": "ocr",
                "campus": campus,
                "category": category,
                "file_name": path.name,
                "file_id": file_id,
                "page": 1,
                "chunk_index": ci,
                "hash": file_hash,
            })
            ids.append(_chunk_id(file_id, 1, ci, ch))
    else:
        return {"file": path.name, "status": "unsupported", "suffix": suffix}

    if not docs:
        return {"file": path.name, "status": "empty_text", "source": source}

    embeddings = embed_model.encode(docs, normalize_embeddings=True).tolist()

    collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    return {"file": path.name, "status": "indexed", "source": source, "chunks": len(docs)}