from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio
import json
import os

app = FastAPI()

# ✅ CORS fix complet pentru Netlify + Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # poți pune aici domeniul Netlify dacă vrei restrictiv
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ✅ Test backend
# =========================
@app.get("/api")
async def root():
    return {"message": "Nexo AI backend is running successfully 🚀"}

# =========================
# ✅ Modele
# =========================
class ChatRequest(BaseModel):
    conversation_id: str
    content: str
    image_data: str | None = None

class Conversation(BaseModel):
    id: str
    title: str

# =========================
# ✅ Rute conversații (simulate)
# =========================
conversations = []

@app.get("/api/conversations")
async def get_conversations():
    return conversations

@app.post("/api/conversations")
async def create_conversation():
    new_conv = {"id": str(len(conversations) + 1), "title": "Conversație Nouă"}
    conversations.append(new_conv)
    return new_conv

# =========================
# ✅ Răspuns AI – endpointul care lipsea
# =========================
@app.post("/api/chat/send")
async def send_message(req: ChatRequest):
    try:
        user_message = req.content

        async def event_stream():
            # Simulare flux de răspuns (streaming text)
            text = f"AI: am primit mesajul tău → {user_message}"
            for c in text:
                yield f"data: {json.dumps({'content': c})}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        return {"error": str(e)}

# =========================
# ✅ Pornire locală
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
