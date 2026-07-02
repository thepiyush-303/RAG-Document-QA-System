from fastapi import FastAPI, UploadFile, Form, File
from contextlib import asynccontextmanager
from database import init_db
import uvicorn
from ingestion import ingest_pdf
from pydantic import BaseModel
from retrieval import get_top_chunks, ask_llm

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("staring up and checking database")
    await init_db()
    yield # The server runs here
    print("Shutting down...")

app = FastAPI(title="RAG Document QA", lifespan=lifespan)

class QueryInput(BaseModel):
    query: str
    user_id: str
    chat_id: str
    top_k: int = 5

@app.get("/")
async def root():
    return {"message": "RAG API is up and running!"}

@app.post("/ingest")
async def handle_ingest( 
    user_id: str = Form(...),
    chat_id: str = Form(...),
    file: UploadFile = File(...)
):
    pdf_bytes = await file.read()
    await ingest_pdf(pdf_bytes, user_id, chat_id)
    return {
        "status": "Success",
        "message": f"PDF '{file.filename}' successfully processed and vectorized."
    }

@app.post("/query")
async def handle_query(req: QueryInput):
    top_chunks = await get_top_chunks(req.query, req.user_id, req.chat_id, req.top_k)
    
    llm_output = await ask_llm(req.query, top_chunks)
    
    return {
        "answer": llm_output["answer"],
        "rationale": llm_output["rationale"],
        "chunks_used": top_chunks
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)