from app.retrieval.retriever import retrieve_documents

query = input(
    "Ask a question: "
)

results = retrieve_documents(
    query,
    top_k=15
)

docs = results["documents"][0]
metas = results["metadatas"][0]
dists = results["distances"][0]

print("\n")
print("=" * 100)
print("TOP RETRIEVAL RESULTS")
print("=" * 100)

for i, (doc, meta, dist) in enumerate(
    zip(docs, metas, dists),
    start=1
):

    print("\n")
    print("=" * 100)
    print(f"RESULT {i}")
    print("=" * 100)

    print(
        "Distance:",
        round(dist, 4)
    )

    print(
        "Source:",
        meta.get(
            "source",
            "unknown"
        )
    )

    print(
        "Chunk ID:",
        meta.get(
            "chunk_id",
            "unknown"
        )
    )

    print("\nPreview:\n")

    print(
        doc[:1500]
    )

    print("\n")