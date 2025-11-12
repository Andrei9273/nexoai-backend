from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import httpx
from pymongo import MongoClient
from bson import ObjectId

# Încarcă .env
load_dotenv()

app = FastAPI()

# === CORS fix ===
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Conexiune MongoDB ===
client = MongoClient(os.getenv("MONGO_URL"))
db = client["ai_assistant_db"]

# === MODELE ===
class Message(BaseModel):
    conversation_id: str
    content: str
    image_data: str | None = None

# === ROUTE TEST ===
@app.get("/api")
def root():
    return {"message": "Nexo AI backend is running successfully 🚀"}

# === ROUTE: Get all conversations ===
@app.get("/api/conversations")
def get_conversations():
    conversations = []
    for c in db.conversations.find():
        conversations.append({
            "id": str(c["_id"]),
            "title": c["title"]
        })
    return conversations

# === ROUTE: Create new conversation ===
@app.post("/api/conversations")
def create_conversation():
    conv = {"title": "Conversație Nouă"}
    result = db.conversations.insert_one(conv)
    return {"id": str(result.inserted_id), "title": conv["title"]}

# === ROUTE: Get all messages ===
@app.get("/api/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str):
    msgs = []
    for m in db.messages.find({"conversation_id": conversation_id}):
        msgs.append({
            "id": str(m["_id"]),
            "role": m["role"],
            "content": m["content"]
        })
    return msgs

# === ROUTE: Chat send ===
@app.post("/api/chat/send")
async def send_message(msg: Message):
    # Salvăm mesajul utilizatorului
    db.messages.insert_one({
        "conversation_id": msg.conversation_id,
        "role": "user",
        "content": msg.content
    })

    # Trimitem la AI real
    ai_response = "⚙️ AI-ul procesează răspunsul..."
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.emergent.run/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('EMERGENT_LLM_KEY')}"},
                json={
                    "model": "claude-3.5-sonnet",
                    "messages": [{"role": "user", "content": msg.content}]
                }
            )
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
            else:
                ai_response = f"❌ Eroare AI ({response.status_code})"
    except Exception as e:
        ai_response = f"❌ Eroare conexiune: {e}"

    # Salvăm răspunsul AI în baza de date
    db.messages.insert_one({
        "conversation_id": msg.conversation_id,
        "role": "assistant",
        "content": ai_response
    })

    return {"reply": ai_response}

