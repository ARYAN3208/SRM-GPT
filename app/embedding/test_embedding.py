import json
import os

from .embedder import (
    create_embedding
)

INPUT_PATH = (
    "app/data/processed/chunked_data.json"
)

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)

embedded_data = []

total = len(data)

for index, item in enumerate(data, start=1):

    text = item.get(
        "text",
        ""
    )

    source = item.get(
        "source",
        "unknown"
    )

    chunk_id = item.get(
        "chunk_id",
        0
    )

    metadata = item.get(
        "metadata",
        {}
    )

    embedding = create_embedding(
        text
    )

    embedded_data.append({

        "text": text,

        "source": source,

        "chunk_id": chunk_id,

        "metadata": metadata,

        "embedding": embedding

    })

    print(
        f"[{index}/{total}] Embedded chunk"
    )

os.makedirs(

    "app/data/embeddings",
    exist_ok=True

)

OUTPUT_PATH = (
    "app/data/embeddings/embedded_data.json"
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        embedded_data,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"Total embeddings: {len(embedded_data)}"
)

print(
    f"Saved to {OUTPUT_PATH}"
)