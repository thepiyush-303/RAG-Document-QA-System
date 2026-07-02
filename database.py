import os
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

qdrant_client = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = "user_pdfs"

async def init_db():
    """Checks if the collection exists, and creates it if it doesn't."""
    # Fetch all existing collections
    collections_response = await qdrant_client.get_collections()
    existing_names = [c.name for c in collections_response.collections]

    if COLLECTION_NAME not in existing_names:
        print(f"Creating Qdrant collection: {COLLECTION_NAME}...")
        await qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384, # The dimension size of the 'all-MiniLM-L6-v2' AI model
                distance=Distance.COSINE
            ),
        )
        print("Collection created successfully!")
    else:
        print(f"Collection '{COLLECTION_NAME}' is ready to go.")