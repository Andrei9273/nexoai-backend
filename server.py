from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import os
import uuid
import json
import base64
import logging
from datetime import datetime, timezone

# === LOAD .ENV ===
load_dotenv(Path(__file__).parent / ".env")

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

print("Loaded Mongo URL:", MONGO_URL)  # DEBUG — vezi exact ce se încarcă
if not MONGO_URL or "mongodb" not in MONGO_URL:
    raise RuntimeError("❌ Mongo URL not loaded properly from .env")

# === INIT MONGO ===
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# === FASTAPI APP ===
app = FastAPI(title="Nexo AI Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


# === MODELS ===
class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    image_data: Optional[str] = None


class Conversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    image_data: Optional[str] = None


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


# === ROUTES ===
@router.get("/")
async def root():
    return {"message": "Nexo AI backend is running successfully 🚀"}


@router.post("/conversations", response_model=Conversation)
async def create_conversation(input: ConversationCreate):
    conv = Conversation(title=input.title)
    doc = conv.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.conversations.insert_one(doc)
    return conv


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    convs = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    for c in convs:
        c["created_at"] = datetime.fromisoformat(c["created_at"])
        c["updated_at"] = datetime.fromisoformat(c["updated_at"])
    return convs


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    await db.messages.delete_many({"conversation_id": conversation_id})
    res = await db.conversations.delete_one({"id": conversation_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(conversation_id: str):
    msgs = await db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    for m in msgs:
        m["timestamp"] = datetime.fromisoformat(m["timestamp"])
    return msgs


@router.post("/chat/send")
async def send_message(input: MessageCreate):
    user_msg = Message(conversation_id=input.conversation_id, role="user", content=input.content, image_data=input.image_data)
    doc = user_msg.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.messages.insert_one(doc)

    await db.conversations.update_one(
        {"id": input.conversation_id},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    # Aici ar fi integrarea AI (GPT, etc.)
    ai_response = f"Echo: {input.content}"

    ai_msg = Message(conversation_id=input.conversation_id, role="assistant", content=ai_response)
    await db.messages.insert_one(ai_msg.model_dump())

    return {"reply": ai_response}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_data = base64.b64encode(contents).decode("utf-8")
        return {"data": base64_data, "filename": file.filename, "type": file.content_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === REGISTER ROUTER ===
app.include_router(router)


# === SHUTDOWN EVENT ===
@app.on_event("shutdown")
async def close_db():
    client.close()


# === LOGGING ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
