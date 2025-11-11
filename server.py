from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# 🔹 Încarcă variabilele din .env
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# 🔹 Inițializează aplicația FastAPI
app = FastAPI()

# ✅ FIX CORS pentru Netlify + local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gregarious-clafoutis-9e1a09.netlify.app",  # Site-ul tău Netlify
        "http://localhost:5173",                            # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Conectare MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

@app.get("/")
def home():
    return {"message": "Nexo AI backend is running successfully 🚀"}

# 🔹 Exemplu de endpoint (poți avea mai multe)
@app.get("/api/conversations")
def get_conversations():
    conversations = list(db.conversations.find({}, {"_id": 1, "title": 1}))
    for c in conversations:
        c["id"] = str(c["_id"])
        del c["_id"]
    return conversations
