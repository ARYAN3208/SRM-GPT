import json
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer

INPUT_CANDIDATES = [
    Path("app/data/processed/chunked_data.json"),
   
]

INPUT_PATH = None
for candidate in INPUT_CANDIDATES:
    if candidate.exists():
        INPUT_PATH = candidate
        break

if INPUT_PATH is None:
    raise FileNotFoundError(
        "Could not find chunked data. Expected one of: "
        + ", ".join(str(path) for path in INPUT_CANDIDATES)
    )

OUTPUT_DIR = (
    "app/data/embeddings"
)

OUTPUT_PATH = (
    f"{OUTPUT_DIR}/embedded_data.json"
)

CHECKPOINT_EVERY = 1000

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

print("Loading embedding model...")

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

print(f"Loading chunks from {INPUT_PATH}...")

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

print(
    f"Chunks Loaded: {len(chunks)}"
)

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
            f"Checkpoint Found: {len(embedded_data)}"
        )

    except:

        embedded_data = []

start_index = len(
    embedded_data
)

BATCH_SIZE = 128

for i in range(
    start_index,
    len(chunks),
    BATCH_SIZE
):

    batch = chunks[
        i:i + BATCH_SIZE
    ]

    texts = [

        item["text"]

        for item in batch
    ]

    embeddings = model.encode(

        texts,

        batch_size=64,

        normalize_embeddings=True,

        show_progress_bar=False

    )

    for item, emb in zip(
        batch,
        embeddings
    ):

        embedded_data.append({

            "text":
            item["text"],

            "source":
            item.get(
                "source",
                ""
            ),

            "chunk_id":
            item.get(
                "chunk_id",
                ""
            ),

            "url":
            item.get(
                "url",
                ""
            ),

            "embedding":
            emb.tolist()

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
            f"Checkpoint Saved: {len(embedded_data)}"
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

print(
    f"Embedding Complete: {len(embedded_data)}"
)

print(
    f"Saved To: {OUTPUT_PATH}"
)