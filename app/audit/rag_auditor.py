from collections import Counter
import hashlib

from utils import (
    FINAL_DIR,
    load_json,
    percentage
)

RAG_FILE = FINAL_DIR / "rag_data.json"


def audit_rag():
    print("\nAuditing RAG Dataset...")

    chunks = load_json(RAG_FILE)

    if not chunks:
        print("rag_data.json not found or empty.")

        return {
            "score": 0,
            "total_chunks": 0,
            "duplicate_chunks": 0,
            "duplicate_chunk_ids": 0,
            "empty_chunks": 0,
            "small_chunks": 0,
            "large_chunks": 0,
            "missing_metadata": 0,
            "average_chunk_length": 0,
            "sources": {}
        }

    total_chunks = len(chunks)

    chunk_ids = set()
    duplicate_chunk_ids = 0

    hashes = set()
    duplicate_chunks = 0

    empty_chunks = 0
    small_chunks = 0
    large_chunks = 0
    missing_metadata = 0

    total_length = 0

    sources = Counter()

    required_fields = [
        "chunk_id",
        "text",
        "source",
        "document_type",
        "chunk_number",
        "total_chunks"
    ]

    for chunk in chunks:

        if not isinstance(chunk, dict):
            continue

        text = chunk.get("text", "").strip()

        total_length += len(text)

        if not text:
            empty_chunks += 1

        if len(text) < 100:
            small_chunks += 1

        if len(text) > 900:
            large_chunks += 1

        chunk_id = chunk.get("chunk_id", "")

        if chunk_id in chunk_ids:
            duplicate_chunk_ids += 1
        else:
            chunk_ids.add(chunk_id)

        text_hash = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

        if text_hash in hashes:
            duplicate_chunks += 1
        else:
            hashes.add(text_hash)

        for field in required_fields:

            if field not in chunk or chunk[field] in ("", None):
                missing_metadata += 1

        sources[chunk.get("source", "Unknown")] += 1

    average_chunk_length = (
        total_length / total_chunks
        if total_chunks
        else 0
    )

    penalties = (
        duplicate_chunks
        + duplicate_chunk_ids
        + empty_chunks
        + missing_metadata
    )

    score = max(
        0,
        round(
            100 - (penalties / max(total_chunks, 1)) * 100,
            2
        )
    )

    print(f"Total Chunks          : {total_chunks}")
    print(f"Duplicate Chunks      : {duplicate_chunks}")
    print(f"Duplicate Chunk IDs   : {duplicate_chunk_ids}")
    print(f"Empty Chunks          : {empty_chunks}")
    print(f"Small Chunks          : {small_chunks}")
    print(f"Large Chunks          : {large_chunks}")
    print(f"Missing Metadata      : {missing_metadata}")
    print(f"Average Chunk Length  : {average_chunk_length:.2f}")
    print(f"Dataset Score         : {score}/100")

    return {
        "score": score,
        "total_chunks": total_chunks,
        "duplicate_chunks": duplicate_chunks,
        "duplicate_chunk_ids": duplicate_chunk_ids,
        "empty_chunks": empty_chunks,
        "small_chunks": small_chunks,
        "large_chunks": large_chunks,
        "missing_metadata": missing_metadata,
        "average_chunk_length": average_chunk_length,
        "sources": dict(sources)
    }