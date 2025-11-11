from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from pydantic import BaseModel
import os

# -------------------------------
# 1️⃣ Încarcă variabilele din .env
# -------------------------------
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# -------------------------------
# 2️⃣ Creează aplicația FastAPI
# -------------------------------
app = FastAPI()

# -------------------------------
# 3️⃣ Activează CORS (Netlify + Local)
# -------------------------------
origins = [
    "https://gregarious-clafoutis-9e1a09.netlify.app",  # site-ul tău Netlify
    "http://localhost:5173",                            # pentru test local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# 4️⃣ Conectare la MongoDB
# -------------------------------
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# -------------------------------
# 5️⃣ MODELE DE DATE
# -------------------------------
class Conversation(BaseModel):
    title: str

class Message(BaseModel):
    conversation_id: str
    role: str
    content: str

# -------------------------------
# 6️⃣ RUTE API
# -------------------------------

@app.get("/")
def home():
    return {"message": "Nexo AI backend is running successfully 🚀"}

@app.get("/api/conversations")
def get_conversations():
    conversations = list(db.conversations.find({}, {"_id": 1, "title": 1}))
    for c in conversations:
        c["id"] = str(c["_id"])
    return conversations

@app.post("/api/conversations")
def create_conversation(conversation: Conversation):
    conv = {"title": conversation.title}
    result = db.conversations.insert_one(conv)
    conv["id"] = str(result.inserted_id)
    return conv

@app.get("/api/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str):
    messages = list(db.messages.find({"conversation_id": conversation_id}))
    for m in messages:
        m["id"] = str(m["_id"])
    return messages

@app.post("/api/chat/send")
def send_message(message: Message):
    db.messages.insert_one({
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content
    })
    return {"status": "ok", "content": f"Mesaj primit: {message.content}"}

@app.post("/api/upload")
async def upload_file(request: Request):
    return {"message": "Imagine încărcată (mock endpoint)"}

# -------------------------------
# 7️⃣ RUN LOCAL (doar pt test)
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
