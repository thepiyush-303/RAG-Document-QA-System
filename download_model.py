from sentence_transformers import SentenceTransformer

print("Downloading embedding model for caching...")
SentenceTransformer("all-MiniLM-L6-v2")
print("Model cached successfully!")