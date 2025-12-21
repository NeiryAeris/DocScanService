# app/api/v1/routers/chat_routes.py
from __future__ import annotations

from typing import List, Optional
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

class AskIn(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None
    top_k: Optional[int] = None  # allow override per request (optional)

@router.post("/ask")
def ask(
    body: AskIn,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    gemini = GeminiClient(
        api_key=config.GEMINI_API_KEY,
        embed_model=config.GEMINI_EMBED_MODEL,
        chat_model=config.GEMINI_CHAT_MODEL,         # ✅ chat needed here
        embed_dims=getattr(config, "GEMINI_EMBED_DIMS", None),  # keep consistent
    )

    store = QdrantStore(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
        collection=config.QDRANT_COLLECTION,
    )

    rag = RAG(gemini_client=gemini, qdrant_store=store, top_k=body.top_k or config.TOP_K)
    return rag.ask(user_id=x_user_id, question=body.question, doc_ids=body.doc_ids)
