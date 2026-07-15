import json
import os

from .metadata_builder import (
    build_metadata
)

INPUT_PATH = (
    "app/05_data/processed/chunked_data.json"
)

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

final_data = []

for chunk in chunks:

    metadata = build_metadata(
        chunk
    )

    final_data.append({

        "text":
        chunk["text"],

        "metadata":
        metadata

    })

os.makedirs(
    "app/05_data/final",
    exist_ok=True
)

output_path = (
    "app/05_data/final/final_rag_data.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final_data,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"Final records: {len(final_data)}"
)

print(
    f"Saved to {output_path}"
)