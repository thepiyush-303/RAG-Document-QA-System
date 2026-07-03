# RAG Document QA System

A FastAPI-based Retrieval Augmented Generation (RAG) service for asking questions over uploaded PDF files.

The application accepts a `user_id`, `chat_id`, and PDF file, extracts text from the PDF, splits it into chunks, embeds those chunks with `all-MiniLM-L6-v2`, and stores them in Qdrant with user/chat metadata. Queries are embedded, matched against the same `user_id` and `chat_id`, and sent to Gemini with the retrieved context.

## Features

- Upload and ingest PDF files through `POST /ingest`
- Extract PDF text with `pypdf`
- Split text into overlapping chunks with LangChain text splitters
- Generate 384-dimensional embeddings with Sentence Transformers
- Store and filter vectors in Qdrant by `user_id` and `chat_id`
- Answer document questions with Gemini
- Simple browser frontend at `/ui`
- No chat-history persistence; the UI only sends the current question to the backend

## Project Structure

```text
.
|-- main.py              # FastAPI app, API routes, frontend mount
|-- database.py          # Qdrant client, collection creation, payload indexes
|-- ingestion.py         # PDF text extraction, chunking, embedding, Qdrant upsert
|-- retrieval.py         # Qdrant retrieval and Gemini answer generation
|-- frontend/
|   |-- index.html       # Upload form and chat layout
|   |-- styles.css       # Basic responsive styling
|   `-- app.js           # Browser logic for /ingest and /query
`-- requirements.txt
```

## Requirements

- Python 3.10+
- A Qdrant instance or Qdrant Cloud cluster
- A Google Gemini API key

## Environment Variables

Create a `.env` file in the project root:

```env
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
```

`database.py` loads `QDRANT_URL` and `QDRANT_API_KEY` with `python-dotenv`. The Gemini SDK reads `GOOGLE_API_KEY` from the environment.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The API will run at:

```text
http://127.0.0.1:8000
```

Open the frontend:

```text
http://127.0.0.1:8000/ui
```

On startup, the app checks Qdrant and creates the `user_pdfs` collection if needed. It also ensures keyword payload indexes exist for `user_id` and `chat_id`.

## API

### Health Check

```http
GET /
```

Response:

```json
{
  "message": "RAG API is up and running!"
}
```

### Ingest PDF

```http
POST /ingest
Content-Type: multipart/form-data
```

Form fields:

- `user_id`: user identifier
- `chat_id`: chat/session identifier
- `file`: PDF file

Example:

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -F "user_id=user-123" \
  -F "chat_id=chat-abc" \
  -F "file=@document.pdf"
```

Response:

```json
{
  "status": "Success",
  "message": "PDF 'document.pdf' successfully processed and vectorized."
}
```

### Query Document

```http
POST /query
Content-Type: application/json
```

Request body:

```json
{
  "query": "What is this document about?",
  "user_id": "user-123",
  "chat_id": "chat-abc",
  "top_k": 5
}
```

Response:

```json
{
  "answer": "Answer generated from the retrieved context.",
  "rationale": "Why the answer follows from the retrieved chunks.",
  "chunks_used": [
    {
      "text": "Retrieved text chunk",
      "score": 0.82
    }
  ]
}
```

## Frontend Flow

1. Enter `user_id` and `chat_id`.
2. Select a PDF file.
3. Submit the upload form.
4. After ingestion completes, ask questions in the message composer.

The frontend does not store chat history. Messages are only kept in browser memory for the current page session.

## Notes

- The embedding model is loaded when `ingestion.py` is imported, so the first startup can take time while the model is downloaded or initialized.
- `top_k` defaults to `5` in the API request model.
- If a PDF has no extractable text, no chunks are inserted into Qdrant.
- The Qdrant vector size is `384`, matching `all-MiniLM-L6-v2`.
