import json
import os

try:
    from .chunker import create_chunks
except ImportError:
    from chunker import create_chunks

INPUT_PATH = "app/data/final/rag_data.json"

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    cleaned_data = json.load(f)

all_chunks = []

for item in cleaned_data:

    text = item.get(
        "cleaned_text",
        item.get("text", "")
    )

    source = item.get(
        "source",
        "unknown"
    )

    if not text.strip():
        continue

    chunks = create_chunks(text)

    for idx, chunk in enumerate(chunks):

        all_chunks.append({

            "source": source,

            "chunk_id": idx,

            "text": chunk

        })

os.makedirs(
    "app/data/processed",
    exist_ok=True
)

output_path = (
    "app/data/processed/chunked_data.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"Total chunks: {len(all_chunks)}"
)

print(
    f"Saved to {output_path}"
)