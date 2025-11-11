from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import json

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "ai_assistant_db")

# Initialize FastAPI app
app = FastAPI()

# ✅ Allow frontend (Netlify) + localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gregarious-clafoutis-9e1a09.netlify.app",  # site-ul tău Netlify
        "http://localhost:5173",  # pentru testare locală
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
conversations = db["conversations"]
messages = db["messages"]

# Models
class Message(BaseModel):
    conversation_id: str
    content: str
    image_data: str | None = None

@app.get("/")
async def root():
    return {"message": "Nexo AI backend is running successfully 🚀"}

@app.get("/api/conversations")
async def get_conversations():
    convs = list(conversations.find())
    for c in convs:
        c["id"] = str(c["_id"])
        del c["_id"]
    return convs

@app.post("/api/conversations")
async def create_conversation():
    new_conv = {"title": "Conversație Nouă"}
    result = conversations.insert_one(new_conv)
    new_conv["id"] = str(result.inserted_id)
    return new_conv

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    messages.delete_many({"conversation_id": conversation_id})
    conversations.delete_one({"_id": ObjectId(conversation_id)})
    return {"status": "deleted"}

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    msgs = list(messages.find({"conversation_id": conversation_id}))
    for m in msgs:
        m["id"] = str(m["_id"])
        del m["_id"]
    return msgs

@app.post("/api/chat/send")
async def send_message(request: Request):
    data = await request.json()
    conversation_id = data.get("conversation_id")
    content = data.get("content", "")
    image_data = data.get("image_data")

    if not conversation_id or not content:
        return JSONResponse({"error": "Mesaj invalid"}, status_code=400)

    # Save user message
    messages.insert_one({
        "conversation_id": conversation_id,
        "role": "user",
        "content": content
    })

    # Simulate AI typing (test)
    async def stream_response():
        yield "data: " + json.dumps({"content": "Salut! 👋 Eu sunt Nexo AI.", "done": False}) + "\n\n"
        await asyncio.sleep(0.5)
        yield "data: " + json.dumps({"content": " Cum pot să te ajut astăzi?", "done": False}) + "\n\n"
        await asyncio.sleep(0.5)
        yield "data: " + json.dumps({"done": True}) + "\n\n"

        # Save assistant reply
        messages.insert_one({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": "Salut! 👋 Eu sunt Nexo AI. Cum pot să te ajut astăzi?"
        })

    return StreamingResponse(stream_response(), media_type="text/event-stream")

@app.post("/api/upload")
async def upload_file(request: Request):
    return {"status": "uploaded"}

