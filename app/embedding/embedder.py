from sentence_transformers import SentenceTransformer

print(
    "Loading embedding model..."
)

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

def create_embedding(text):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()