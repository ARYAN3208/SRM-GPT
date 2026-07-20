import json
import os
from pathlib import Path

from embedder import create_embeddings

INPUT_PATH = Path("app/data/final/rag_data.json")

OUTPUT_DIR = "app/data/embeddings"

OUTPUT_PATH = f"{OUTPUT_DIR}/embedded_data.json"

CHECKPOINT_EVERY = 1000

BATCH_SIZE = 256

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

print("Loading chunks...")

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

print(f"Chunks Loaded : {len(chunks)}")

embedded_data = []

if Path(
    OUTPUT_PATH
).exists():

    try:

        with open(
            OUTPUT_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            embedded_data = json.load(f)

        print(
            f"Checkpoint Found : {len(embedded_data)}"
        )

    except:

        embedded_data = []

start = len(
    embedded_data
)

for i in range(
    start,
    len(chunks),
    BATCH_SIZE
):

    batch = chunks[
        i:i+BATCH_SIZE
    ]

    texts = [
        item["text"]
        for item in batch
    ]

    embeddings = create_embeddings(
        texts,
        batch_size=BATCH_SIZE
    )

    for item, emb in zip(
        batch,
        embeddings
    ):

        embedded_data.append({

            "chunk_id":
            item["chunk_id"],

            "text":
            item["text"],

            "source":
            item["source"],

            "document_type":
            item.get(
                "document_type",
                ""
            ),

            "url":
            item.get(
                "url",
                ""
            ),

            "title":
            item.get(
                "title",
                ""
            ),

            "file_name":
            item.get(
                "file_name",
                ""
            ),

            "chunk_number":
            item.get(
                "chunk_number",
                0
            ),

            "total_chunks":
            item.get(
                "total_chunks",
                0
            ),

            "embedding":
            emb

        })

    if len(
        embedded_data
    ) % CHECKPOINT_EVERY == 0:

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                embedded_data,
                f,
                ensure_ascii=False
            )

        print(
            f"Checkpoint Saved : {len(embedded_data)}"
        )

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        embedded_data,
        f,
        ensure_ascii=False
    )

print()

print("=" * 60)

print("Embedding Complete")

print("=" * 60)

print(
    f"Total Embedded : {len(embedded_data)}"
)

print(
    f"Saved To : {OUTPUT_PATH}"
)