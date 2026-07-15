import json

try:
    from .chroma_store import (
        add_documents,
        get_collection_count
    )
except ImportError:
    from chroma_store import (
        add_documents,
        get_collection_count
    )

INPUT_PATH = (
    "app/data/embeddings/embedded_data.json"
)

print("Loading embeddings...")

with open(
    INPUT_PATH,
    "r",
    encoding="utf-8"
) as f:

    embedded_data = json.load(f)

print(
    f"Records found: {len(embedded_data)}"
)

add_documents(
    embedded_data
)

print(
    f"Collection count: {get_collection_count()}"
)