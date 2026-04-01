"""
FastAPI server — exposes the orchestrator over HTTP.

Endpoints:
  POST /session/start        → create a new session
  POST /session/{id}/chat    → send a chat message
  POST /session/{id}/generate → trigger the content pipeline (with optional image)
  GET  /session/{id}/result  → retrieve the final result
  GET  /health               → health check
"""

import base64
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import MarketingOrchestrator

app = FastAPI(title="Marketing Content Generator API", version="1.0.0")

# Allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://capstone-frontend-088441258688.s3-website-us-east-1.amazonaws.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (replace with Redis / DB in production)
_sessions: dict[str, MarketingOrchestrator] = {}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    phase: str
    collected: dict[str, Any] | None = None


class GenerateResponse(BaseModel):
    session_id: str
    phase: str
    collected_data: dict[str, Any]
    content_plan: dict[str, Any]
    captions: list[dict[str, Any]]
    image: dict[str, Any]
    validation: dict[str, Any] | None = None
    revision_histories: dict[str, Any] | None = None


class RefineCaptionRequest(BaseModel):
    variation_index: int   # 0 = Variation A, 1 = B, 2 = C
    feedback: str


class RefineImageRequest(BaseModel):
    feedback: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/session/start")
def start_session() -> dict[str, str]:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = MarketingOrchestrator()
    return {"session_id": session_id}


@app.post("/session/{session_id}/chat", response_model=ChatResponse)
def chat(session_id: str, body: ChatRequest) -> ChatResponse:
    """Send a user message to the chat agent."""
    orchestrator = _get_session(session_id)

    if orchestrator.phase not in ("chat", "pipeline_ready"):
        raise HTTPException(400, "Chat phase is over. Call /generate to proceed.")

    turn = orchestrator.run_chat_turn(body.message)
    return ChatResponse(
        session_id=session_id,
        reply=turn["reply"],
        phase=turn["phase"],
        collected=turn["collected"],
    )


@app.post("/session/{session_id}/generate", response_model=GenerateResponse)
async def generate(
    session_id: str,
    image: UploadFile | None = File(default=None),
) -> GenerateResponse:
    """
    Trigger the content pipeline.
    Optionally attach an image file (multipart/form-data).
    """
    orchestrator = _get_session(session_id)

    if orchestrator.phase == "chat":
        raise HTTPException(400, "Complete the chat phase first.")

    if orchestrator.phase == "complete":
        # Return cached result
        result = orchestrator._build_output()
        return GenerateResponse(session_id=session_id, **result)

    # Process uploaded image if provided
    image_b64: str | None = None
    media_type = "image/jpeg"

    if image and image.filename:
        raw = await image.read()
        image_b64 = base64.b64encode(raw).decode()
        media_type = image.content_type or "image/jpeg"

    result = orchestrator.run_content_pipeline(image_b64, media_type)
    return GenerateResponse(session_id=session_id, **result)


@app.post("/session/{session_id}/refine/caption")
def refine_caption(session_id: str, body: RefineCaptionRequest) -> dict[str, Any]:
    """Refine a specific caption variation based on user feedback."""
    orchestrator = _get_session(session_id)
    if orchestrator.phase != "complete":
        raise HTTPException(400, "Run /generate first.")
    if not (0 <= body.variation_index <= 2):
        raise HTTPException(400, "variation_index must be 0, 1, or 2.")
    return orchestrator.refine_caption_variation(body.variation_index, body.feedback)


@app.post("/session/{session_id}/refine/image")
def refine_image(session_id: str, body: RefineImageRequest) -> dict[str, Any]:
    """Regenerate the image based on user feedback."""
    orchestrator = _get_session(session_id)
    if orchestrator.phase != "complete":
        raise HTTPException(400, "Run /generate first.")
    if orchestrator.image_result.get("mode") != "generate":
        raise HTTPException(400, "Image refinement only works for generated images, not uploaded ones.")
    return orchestrator.refine_image(body.feedback)


@app.get("/session/{session_id}/result", response_model=GenerateResponse)
def get_result(session_id: str) -> GenerateResponse:
    """Retrieve the result of a completed pipeline run."""
    orchestrator = _get_session(session_id)
    if orchestrator.phase != "complete":
        raise HTTPException(400, "Pipeline not yet complete.")
    result = orchestrator._build_output()
    return GenerateResponse(session_id=session_id, **result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id: str) -> MarketingOrchestrator:
    if session_id not in _sessions:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
