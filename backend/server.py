import time
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.generator.rag_pipeline import ask_rag
from app.utils.logger import get_logger
logger = get_logger("campusgpt.server")

app = FastAPI(
    title="SRM CampusGPT API",
    version="1.0.0"
)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def no_cache_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(frontend_dir / "index.html")

else:
    print(f"WARNING: frontend directory not found at {frontend_dir}")

_sessions: dict[str, list[dict]] = {}

ALLOWED_MODELS = Literal[
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "llama-3.3-70b",
    "ollama:deepseek-r1:14b",
    "ollama:gemma4:e2b",
    "ollama:llama3:8b",
    "ollama:mistral:latest",
    "ollama:phi3:mini",
    "ollama:gemma2:2b",
]

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    model_name: ALLOWED_MODELS = "gemini-2.5-flash"

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    confidence: float
    confidence_label: str
    docs_info: list
    response_time: float
    model_used: str

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    logger.info(
        "Incoming chat request | session_id=%s | model_name=%r | message=%r",
        session_id,
        req.model_name,
        req.message[:80],
    )

    try:
        result = ask_rag(
            question=req.message,
            model_name=req.model_name
        )
    except Exception as e:
        logger.exception("Pipeline error for model_name=%r", req.model_name)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    history = _sessions.setdefault(session_id, [])
    history.append({
        "role": "user",
        "content": req.message,
        "ts": time.time()
    })
    history.append({
        "role": "assistant",
        "content": result["answer"],
        "ts": time.time()
    })

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        confidence=result.get("confidence", 0),
        confidence_label=result.get("confidence_label", "Low"),
        docs_info=result.get("docs_info", []),
        response_time=result.get("response_time", 0),
        model_used=req.model_name,
    )

@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    return {"session_id": session_id, "messages": _sessions.get(session_id, [])}

@app.delete("/api/history/{session_id}")
def clear_history(session_id: str):
    _sessions.pop(session_id, None)
    return {"status": "cleared"}