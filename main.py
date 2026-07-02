from fastapi import FastAPI
import uvicorn

app = FastAPI(title="RAG PDF Assistant")

@app.get("/")
async def root():
    return {"message": "RAG API is up and running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)