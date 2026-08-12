"""
app.py
------
FastAPI web server for the ShopEasy support agent.

Routes:
  GET  /        -> live-chat support console (index.html)
  GET  /pitch   -> client pitch page (pitch.html)
  POST /chat    -> send a customer message, get the agent's reply
  GET  /health  -> health check

Run from the backend/ folder:  uvicorn app:app --reload
Then open:                     http://127.0.0.1:8000
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import get_reply

app = FastAPI(title="ShopEasy Support AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/")
def home():
    # The pitch page is the landing page now.
    return FileResponse(os.path.join(FRONTEND_DIR, "pitch.html"))


@app.get("/demo")
def demo():
    # The live chat console.
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/chat")
def chat(payload: ChatIn):
    # LangGraph remembers history per session_id, so we just pass the new message.
    reply = get_reply(payload.session_id, payload.message)
    return {"reply": reply}


@app.get("/health")
def health():
    return {"status": "ok"}
