from pypdf import PdfReader
from io import BytesIO
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
from database import qdrant_client, COLLECTION_NAME

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    # BytesIO lets Python treat a stream of raw bytes exactly like an open file on your disk
    pdf_file = BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    return text

def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )
    return splitter.split_text(text)

async def ingest_pdf(pdf_bytes: bytes, user_id: str, chat_id: str):
    
    raw_text = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(raw_text)

    if not chunks:
        return
    
    embeddings = embedding_model.encode(chunks)

    points = []
    for i, chunk in enumerate(chunks):
        point_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id= point_id,
                vector= embeddings[i].tolist(),
                payload={
                    "text": chunk,
                    "user_id": user_id,
                    "chat_id": chat_id
                }
            )
        )
    
    await qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"Successfully ingested {len(points)} chunks into Qdrant.")
