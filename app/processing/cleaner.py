import re
import hashlib
import unicodedata


MIN_DOCUMENT_LENGTH = 20


def normalize_text(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", " ")
    text = text.replace("\ufeff", " ")

    text = re.sub(r"\.{5,}", " ", text)
    text = re.sub(r"…{3,}", " ", text)
    text = re.sub(r"·{3,}", " ", text)
    text = re.sub(r"[_=\-]{4,}", " ", text)
    text = re.sub(r"[|~]{4,}", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_text(item):
    if not isinstance(item, dict):
        return ""

    if "pages" in item:
        parts = []

        for page in item.get("pages", []):
            if isinstance(page, dict):
                text = page.get("text", "")
                if text:
                    parts.append(text)

        return "\n\n".join(parts)

    return (
        item.get("text")
        or item.get("content")
        or ""
    )


def is_garbled(text):
    if len(text) < MIN_DOCUMENT_LENGTH:
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


def document_hash(text):
    return hashlib.sha256(
        normalize_text(text).encode("utf-8")
    ).hexdigest()


def clean_record(item, source):
    text = normalize_text(extract_text(item))

    if len(text) < MIN_DOCUMENT_LENGTH:
        return None

    if is_garbled(text):
        return None

    return {
        "text": text,
        "source": source,
        "document_type": "pdf" if "pdf" in source.lower() else "website",
        "url": item.get("url", "").strip(),
        "title": item.get("title", "").strip(),
        "file_name": item.get("file", "").strip()
    }


def remove_duplicate_documents(records):
    unique = []

    seen_urls = set()
    seen_files = set()
    seen_hashes = set()

    for record in records:

        url = record["url"]
        file_name = record["file_name"]
        text_hash = document_hash(record["text"])

        if text_hash in seen_hashes:
            continue

        if url and url in seen_urls:
            continue

        if file_name and file_name in seen_files:
            continue

        seen_hashes.add(text_hash)

        if url:
            seen_urls.add(url)

        if file_name:
            seen_files.add(file_name)

        unique.append(record)

    return unique


def clean_documents(records, source):
    cleaned = []

    for item in records:
        if not isinstance(item, dict):
            continue

        record = clean_record(item, source)

        if record:
            cleaned.append(record)

    return remove_duplicate_documents(cleaned)
