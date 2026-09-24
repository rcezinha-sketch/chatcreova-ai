from __future__ import annotations

import importlib.util
import json
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.5:4b"


def load_local_module(name: str, filename: str):
    path = BASE_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_service = load_local_module(
    "chatcreova_v23_context_api",
    "V23-context-service.py",
)

app = FastAPI(
    title="ChatCreova AI V23 API",
    version="23.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "local_user"
    project_id: str = "default_project"
    project_name: str = "ChatCreova AI"
    session_id: str | None = None
    recent_messages: list[dict[str, Any]] | None = None


def call_ollama(
    messages: list[dict[str, str]],
) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "20m",
        "options": {
            "num_predict": 900,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=600,
    ) as response:
        body = response.read().decode("utf-8")

    result = json.loads(body)

    answer = (
        result
        .get("message", {})
        .get("content", "")
        .strip()
    )

    if not answer:
        raise RuntimeError(
            "O Ollama terminou sem resposta."
        )

    return answer


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "ChatCreova V23 API",
        "queen": True,
        "model": MODEL,
    }


@app.post("/api/chat")
def chat(
    req: ChatRequest,
) -> dict[str, Any]:
    message = req.message.strip()

    if not message:
        return {
            "ok": False,
            "type": "error",
            "message": "Digite uma mensagem.",
        }

    try:
        packet = (
            context_service
            .build_context_packet(
                user_text=message,
                user_id=req.user_id,
                project_id=req.project_id,
                project_name=req.project_name,
                session_id=req.session_id,
                recent_messages=req.recent_messages,
            )
        )

    except (
        context_service
        .ContextReferenceError
    ) as exc:
        return {
            "ok": True,
            "type": "clarification",
            "assistant": "Queen",
            "message": str(exc),
        }

    messages = (
        context_service
        .context_packet_to_messages(
            packet
        )
    )

    try:
        answer = call_ollama(messages)

    except Exception as exc:
        return {
            "ok": False,
            "type": "engine_error",
            "assistant": "Queen",
            "message": (
                "Não foi possível acessar "
                "o motor local Ollama."
            ),
            "detail": str(exc),
        }

    return {
        "ok": True,
        "type": "answer",
        "assistant": "Queen",
        "message": answer,
        "context_packet_id": (
            packet.get(
                "context_packet_id"
            )
        ),
    }
