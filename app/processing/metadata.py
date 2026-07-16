import hashlib


REQUIRED_FIELDS = [
    "text",
    "source",
    "document_type",
    "url",
    "title",
    "file_name",
    "chunk_number",
    "total_chunks",
    "chunk_length"
]


def generate_chunk_id(chunk):
    key = "|".join([
        chunk.get("source", ""),
        chunk.get("url", ""),
        chunk.get("file_name", ""),
        str(chunk.get("chunk_number", "")),
        chunk.get("text", "")
    ])

    return hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()


def validate_chunk(chunk):
    for field in REQUIRED_FIELDS:
        if field not in chunk:
            return False

    if not chunk["text"].strip():
        return False

    return True


def build_metadata(chunks):
    final_chunks = []

    seen_ids = set()

    for chunk in chunks:

        if not validate_chunk(chunk):
            continue

        chunk_id = generate_chunk_id(chunk)

        if chunk_id in seen_ids:
            continue

        seen_ids.add(chunk_id)

        final_chunks.append({
            "chunk_id": chunk_id,
            "text": chunk["text"],
            "source": chunk["source"],
            "document_type": chunk["document_type"],
            "url": chunk["url"],
            "title": chunk["title"],
            "file_name": chunk["file_name"],
            "chunk_number": chunk["chunk_number"],
            "total_chunks": chunk["total_chunks"],
            "chunk_length": chunk["chunk_length"]
        })

    return final_chunks
