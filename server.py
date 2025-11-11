from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os

app = FastAPI()

# === CORS ===
origins = [
    "https://gregarious-clafoutis-9e1a09.netlify.app",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DATABASE ===
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000, tls=True)
    db = client[DB_NAME]
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# === MODELS ===
class Conversation(BaseModel):
    title: str

# === ROUTES ===
@app.get("/")
def home():
    return {"message": "Nexo AI backend is running successfully 🚀"}

@app.post("/api/conversations")
def create_conversation(conv: Conversation):
    try:
        result = db.conversations.insert_one({"title": conv.title})
        return {"id": str(result.inserted_id), "title": conv.title}
    except Exception as e:
        return {"error": f"Failed to insert conversation: {str(e)}"}

@app.get("/api/conversations")
def get_conversations():
    try:
        conversations = list(db.conversations.find({}, {"_id": 1, "title": 1}))
        return [{"id": str(c["_id"]), "title": c["title"]} for c in conversations]
    except Exception as e:
        return {"error": f"Failed to fetch conversations: {str(e)}"}
