# app/api/v1/routers/chat_routes.py
from __future__ import annotations

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.core.deps import verify_internal_token
from app.core import config
from app.services.llm.gemini_client import GeminiClient
from app.services.vector.qdrant_store import QdrantStore
from app.pipelines.rag import RAG


router = APIRouter(
    prefix="/internal/chat",
    tags=["chat"],
    dependencies=[Depends(verify_internal_token)],
)

from pydantic import BaseModel, Field

class HistoryItem(BaseModel):
    # Android uses role="model" for assistant messages.
    # Accept it here to avoid FastAPI returning 422.
    role: Literal["user", "assistant", "system", "model"] = "user"
    text: str = Field(..., min_length=1)

class AskIn(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None
    top_k: Optional[int] = None
    mode: Literal["auto", "doc", "general"] = "auto"
    history: Optional[List[HistoryItem]] = None
    min_score: Optional[float] = None  # override config.RAG_MIN_SCORE

@router.post("/ask")
def ask(
    body: AskIn,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    gemini = GeminiClient(
        api_key=config.GEMINI_API_KEY,
        embed_model=config.GEMINI_EMBED_MODEL,
        chat_model=config.GEMINI_CHAT_MODEL,
        embed_dims=getattr(config, "GEMINI_EMBED_DIMS", None),
        max_output_tokens=getattr(config, "GEMINI_MAX_OUTPUT_TOKENS", 1024),
        temperature=getattr(config, "GEMINI_TEMPERATURE", 0.2),
    )

    store = QdrantStore(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
        collection=config.QDRANT_COLLECTION,
    )

    rag = RAG(
        gemini_client=gemini,
        qdrant_store=store,
        top_k=body.top_k or config.TOP_K,
        min_score=(body.min_score if body.min_score is not None else getattr(config, "RAG_MIN_SCORE", 0.2)),
        general_system_prompt=getattr(config, "GENERAL_CHAT_SYSTEM_PROMPT", "You are a helpful assistant."),
    )

    history = [m.model_dump() for m in (body.history or [])] or None
    # Normalize role "model" -> "assistant" so downstream formatting is correct.
    if history:
        for m in history:
            if (m.get("role") or "").lower() == "model":
                m["role"] = "assistant"
    return rag.ask(
        user_id=x_user_id,
        question=body.question,
        doc_ids=body.doc_ids,
        mode=body.mode,
        history=history,
    )
