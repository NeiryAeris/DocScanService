from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.core.deps import verify_internal_token
from app.core import config
from app.services.llm.gemini_client import GeminiClient
from app.services.vector.qdrant_store import QdrantStore
from app.pipelines.indexer import Indexer
from app.pipelines.chunk import PageText


router = APIRouter(
    prefix="/internal/index",
    tags=["index"],
    dependencies=[Depends(verify_internal_token)],
)

class PageIn(BaseModel):
    page_number: int
    text: str

class UpsertOcrIn(BaseModel):
    doc_id: str
    title: Optional[str] = None
    pages: List[PageIn]

@router.post("/upsert_ocr")
def upsert_ocr(
    body: UpsertOcrIn,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    gemini = GeminiClient(
        api_key=config.GEMINI_API_KEY,
        chat_model=None,
        embed_model=config.GEMINI_EMBED_MODEL,
    )
    store = QdrantStore(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
        collection=config.QDRANT_COLLECTION,
    )

    indexer = Indexer(
        gemini_client=gemini,
        qdrant_store=store,
        chunk_size=config.CHUNK_SIZE,
        overlap=config.CHUNK_OVERLAP,
    )

    pages = [PageText(p.page_number, p.text) for p in body.pages]
    return indexer.upsert_ocr(user_id=x_user_id, doc_id=body.doc_id, title=body.title, pages=pages)
