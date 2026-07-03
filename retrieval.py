import os
import json
from google import genai
from google.genai import types
from qdrant_client.http import models

from database import qdrant_client, COLLECTION_NAME
from ingestion import embedding_model 

genai_client = genai.Client()

async def get_top_chunks(query: str, user_id: str, chat_id: str, top_k: int = 5) -> list:
    """Searches Qdrant for the most relevant text chunks using metadata filtering."""
    
    # Convert the user's text question into a vector array
    query_vector = embedding_model.encode(query).tolist()
    
    print("Searching Qdrant for chunks...")

    search_results = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                models.FieldCondition(key="chat_id", match=models.MatchValue(value=chat_id)),
            ]
        ),
        limit=top_k
    )
    
    return [{"text": point.payload.get("text"), "score": point.score} for point in search_results.points]

async def ask_llm(query: str, chunks: list) -> dict:
    """Constructs the prompt with context and calls the Gemini LLM."""
    print("Calling Gemini model...")
    
    context = "\n\n---\n\n".join([c["text"] for c in chunks])
    
    prompt = f"""
    You are a document assistant. Answer the user's question using ONLY the context provided below.
    Always respond in valid JSON format only.
    If the answer is not found, state that in the rationale.

    -------------------
    Context:
    {context}
    -------------------

    Question:
    {query}

    Respond in this exact format:
    {{
      "answer": "string",
      "rationale": "string"
    }}
    """

    response = await genai_client.aio.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2, 
            response_mime_type="application/json" 
        )
    )
    
    reply = response.text.strip()
    print("Gemini raw reply:", reply)
    
    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        return {
            "answer": reply,
            "rationale": "Model returned non-JSON text; using fallback mode."
        }