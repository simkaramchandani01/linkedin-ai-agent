from sentence_transformers import SentenceTransformer

# Use a small, fast model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_text_embedding(text: str):
    """
    Returns a 384-dimensional embedding of a text string.
    """
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding
