import json
import chromadb

DB_PATH = "app/data/chroma_db"
COLLECTION_NAME = "srm_knowledge_base"

print("Loading embeddings...")

with open(
    "app/data/embeddings/embedded_data.json",
    "r",
    encoding="utf-8"
) as f:

    embedded_data = json.load(f)

print(
    f"Embeddings Loaded: {len(embedded_data)}"
)

client = chromadb.PersistentClient(
    path=DB_PATH
)

try:

    client.delete_collection(
        COLLECTION_NAME
    )

    print(
        "Old collection deleted."
    )

except Exception:

    print(
        "No old collection found."
    )

from app.vector_db.chroma_store import (
    add_documents,
    get_collection_count
)

print(
    "Creating new collection..."
)

add_documents(
    embedded_data
)

print(
    f"Final Chroma Count: {get_collection_count()}"
)