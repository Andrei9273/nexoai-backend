from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os

app = FastAPI()

# --- CORS CONFIG ---
origins = [
    "http://localhost:5173",
    "https://gregarious-clafoutis-9e1a09.netlify.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE CONFIG ---
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URL, tls=True)
db = client[DB_NAME]

# --- MODELS ---
class Conversation(BaseModel):
    title: str

class Message(BaseModel):
    conversation_id: str
    role: str
    content: str

# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "Nexo AI backend is running successfully 🚀"}

@app.post("/api/conversations")
def create_conversation(conv: Conversation):
    try:
        result = db.conversations.insert_one({"title": conv.title})
        return {"id": str(result.inserted_id), "title": conv.title}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/conversations")
def get_conversations():
    conversations = list(db.conversations.find({}, {"_id": 1, "title": 1}))
    return [{"id": str(c["_id"]), "title": c["title"]} for c in conversations]
