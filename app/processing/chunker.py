import hashlib
import re

CHUNK_SIZE = 650
OVERLAP = 100
MIN_CHUNK_LENGTH = 80


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    return [
        s.strip()
        for s in re.split(r"(?<=[.!?।])\s+", text)
        if s.strip()
    ]


def build_chunks(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        paragraphs = [text]

    chunks = []

    for paragraph in paragraphs:

        sentences = split_sentences(paragraph)

        current = ""

        for sentence in sentences:

            if not current:
                current = sentence
                continue

            if len(current) + len(sentence) + 1 <= chunk_size:
                current += " " + sentence
            else:
                chunks.append(current.strip())

                words = current.split()
                overlap_words = []

                while words and len(" ".join(overlap_words)) < overlap:
                    overlap_words.insert(0, words.pop())

                current = (" ".join(overlap_words) + " " + sentence).strip()

        if current:
            chunks.append(current.strip())

    return [c for c in chunks if len(c) >= MIN_CHUNK_LENGTH]


def chunk_hash(text):
    return hashlib.sha256(
        re.sub(r"\s+", " ", text.strip()).encode("utf-8")
    ).hexdigest()


def remove_duplicate_chunks(chunks):
    unique = []
    seen = set()

    for chunk in chunks:
        h = chunk_hash(chunk)

        if h in seen:
            continue

        seen.add(h)
        unique.append(chunk)

    return unique


def chunk_documents(documents):
    final_chunks = []

    for document in documents:

        chunks = build_chunks(document["text"])
        chunks = remove_duplicate_chunks(chunks)

        total = len(chunks)

        for index, chunk in enumerate(chunks, start=1):
            final_chunks.append({
                "text": chunk,
                "source": document["source"],
                "document_type": document["document_type"],
                "url": document["url"],
                "title": document["title"],
                "file_name": document["file_name"],
                "chunk_number": index,
                "total_chunks": total,
                "chunk_length": len(chunk)
            })

    return final_chunks
