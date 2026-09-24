from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent


def load_local_module(name, filename):
    path = BASE_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_service = load_local_module(
    "chatcreova_v23_context_api",
    "V23-context-service.py"
)

app = FastAPI(title="ChatCreova AI V23 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "local_user"
    project_id: str = "default_project"


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "ChatCreova V23 API",
        "queen": True
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        packet = context_service.build_context_packet(
            user_text=req.message,
            user_id=req.user_id,
            project_id=req.project_id
        )
    except context_service.ContextReferenceError as exc:
        return {
            "ok": True,
            "type": "clarification",
            "assistant": "Queen",
            "message": str(exc)
        }

    return {
        "ok": True,
        "type": "context_ready",
        "assistant": "Queen",
        "context_packet_id": packet.get("context_packet_id")
    }
