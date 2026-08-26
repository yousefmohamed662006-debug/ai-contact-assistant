"""
FastAPI Server for AI Contact Assistant
Provides REST API endpoints and serves the Web UI.
"""

import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.ai_agent import ContactAIAgent
from engine.matcher import ContactMatcher

app = FastAPI(
    title="AI Executive Contact Assistant API",
    description="Intelligent bilingual employee search and directory engine.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ContactAIAgent()
matcher = ContactMatcher()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    api_key: Optional[str] = None
    mode: Optional[str] = "offline"


class ChatResponse(BaseModel):
    reply: str
    language: Optional[str] = "ar"
    status: Optional[str] = "none"
    contacts: Optional[List[Dict[str, Any]]] = []
    engine_mode: Optional[str] = "local_offline"
    failover: Optional[bool] = False


class SetKeyRequest(BaseModel):
    api_key: str


class SetModeRequest(BaseModel):
    mode: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Processes user query, executes hybrid search, and returns AI response + matched cards."""
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    if payload.api_key:
        agent.set_api_key(payload.api_key)

    result = agent.process_query(payload.message, mode=payload.mode)
    return ChatResponse(**result)


@app.get("/api/contacts")
async def list_contacts(
    search: Optional[str] = None,
    department: Optional[str] = None,
    building: Optional[str] = None,
    lang: str = "ar"
):
    """Returns all contacts or filtered contacts for table/directory views."""
    contacts = matcher.get_all_contacts(lang=lang)
    
    if department:
        contacts = [c for c in contacts if c.get("department_code") == department.lower()]
    if building:
        contacts = [c for c in contacts if c.get("building") == building.upper()]
    if search:
        search_res = matcher.search(search)
        contacts = search_res["matches"]

    return {
        "count": len(contacts),
        "language": lang,
        "contacts": contacts
    }


@app.post("/api/set-api-key")
async def set_gemini_key(payload: SetKeyRequest):
    """Allows user to plug in their free Gemini API Key live from UI."""
    agent.set_api_key(payload.api_key.strip())
    return {"status": "success", "message": "API key updated successfully."}


@app.post("/api/set-mode")
async def set_engine_mode(payload: SetModeRequest):
    """Switches the operating mode between online and offline."""
    agent.set_mode(payload.mode)
    return {"status": "success", "mode": payload.mode}


@app.get("/api/health")
async def health_check():
    """System health & status check."""
    return {
        "status": "healthy",
        "contacts_loaded": len(matcher.contacts),
        "gemini_active": bool(agent.api_key),
        "active_mode": agent.force_mode,
        "default_engine": "Gemini 1.5 Flash (Online)" if (agent.api_key and agent.force_mode == "online") else "Smart Local Hybrid Engine (Offline)"
    }


# Mount Web UI directory as static files
WEB_DIR = os.path.join(BASE_DIR, "web")
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(WEB_DIR, "index.html"))
