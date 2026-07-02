from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("staring up and checking database")
    await init_db()
    yield # The server runs here
    print("Shutting down...")

app = FastAPI(title="RAG Document QA", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "RAG API is up and running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)