from sentence_transformers import SentenceTransformer

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2"
)

print(model.get_sentence_embedding_dimension())
print("Embedding model loaded.")


def create_embedding(text):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def create_embeddings(texts, batch_size=256):

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embeddings.tolist()


def create_query_embedding(query):

    embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    return embedding.tolist()