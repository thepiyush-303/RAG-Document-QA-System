import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from ingestion import embedding_model
from database import qdrant_client, COLLECTION_NAME
from qdrant_client.http import models
import re
import json

load_dotenv()


llm_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

async def get_top_chunks(user_id: str, chat_id: str, query: str, top_k: int = 5) -> list:
    # Convert the user's text question into a vector array
    query_vector = embedding_model.encode(query).to_list()

    search_results = await qdrant_client.query_points(
        collection_name= COLLECTION_NAME,
        query= query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                models.FieldCondition(key="chat_id", match=models.MatchValue(value=chat_id)),
            ]
        ),
        limit= top_k
    )
    return [{"text": point.payload.get("text"), "score": point.score} for point in search_results.points]

async def ask_llm(query: str, chunks: list) -> dict:
    """Constructs the prompt with context and calls the LLM."""
    
    # Mash all the retrieved text chunks together into one big string
    context = "\n\n---\n\n".join([c["text"] for c in chunks])
    
    prompt = f"""
    You are a document assistant. Answer the user's question using ONLY the context provided below.
    Always respond in valid JSON format only, with no extra markdown or commentary.
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
    
    # Call the DeepSeek model
    response = await llm_client.chat.completions.create(
        model="deepseek/deepseek-chat-v3.1:free", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, # Low temperature keeps the model focused on facts, not creativity
    )
    
    reply = response.choices[0].message.content.strip()
    
    # Safely extract the JSON using a regular expression
    json_match = re.search(r'\{[\s\S]*\}', reply)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
            
    # Fallback if the LLM ignores instructions and returns plain text
    return {
        "answer": reply,
        "rationale": "Model returned non-JSON text; using fallback mode."
    }
