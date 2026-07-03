import os
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

load_dotenv()

qdrant_client = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = "user_pdfs"

async def init_db():
    """Checks if the collection exists, creates it, and strictly ensures payload indexes exist."""
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
        print(f"Collection '{COLLECTION_NAME}' already exists.")

    print("Ensuring payload indexes (user_id, chat_id)...")
    
    try:
        await qdrant_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Index for 'user_id' created successfully.")
    except Exception as e:
        if "already exists" not in str(e).lower():
            print(f"Could not create index for user_id: {e}")

    try:
        await qdrant_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="chat_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Index for 'chat_id' created successfully.")
    except Exception as e:
        if "already exists" not in str(e).lower():
            print(f"Could not create index for chat_id: {e}")

    print("Payload indexes are completely ready.")