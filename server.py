from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
mongo_url = os.getenv("MONGO_URL")
db_name = os.getenv("DB_NAME", "ai_assistant_db")
client = MongoClient(mongo_url)
db = client[db_name]
conversations = db["conversations"]
messages = db["messages"]

# LLM API key
LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# Models
class ChatMessage(BaseModel):
    conversation_id: str
    content: str

@app.get("/")
async def root():
    return {"message": "✅ Nexo AI backend is running successfully"}

@app.get("/api/conversations")
async def get_conversations():
    data = []
    for conv in conversations.find():
        data.append({"id": str(conv["_id"]), "title": conv["title"]})
    return data

@app.post("/api/conversations")
async def create_conversation():
    conv = {"title": "Conversație Nouă"}
    result = conversations.insert_one(conv)
    return {"id": str(result.inserted_id), "title": conv["title"]}

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    data = []
    for msg in messages.find({"conversation_id": conversation_id}):
        data.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "content": msg["content"]
        })
    return data

@app.post("/api/chat/send")
async def send_message(request: Request):
    body = await request.json()
    conv_id = body.get("conversation_id")
    user_message = body.get("content")

    # Save user message
    messages.insert_one({
        "conversation_id": conv_id,
        "role": "user",
        "content": user_message
    })

    # 🔥 Generate AI reply via Emergent LLM API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.emergent.llm/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "emergent-large",
                "messages": [
                    {"role": "system", "content": "You are Nexo AI, a helpful assistant created by Andrei."},
                    {"role": "user", "content": user_message}
                ]
            }
        )

    data = response.json()
    ai_reply = data.get("choices", [{}])[0].get("message", {}).get("content", "Nexo AI: răspuns indisponibil 🫣")

    # Save AI reply
    messages.insert_one({
        "conversation_id": conv_id,
        "role": "assistant",
        "content": ai_reply
    })

    return {"response": ai_reply}
