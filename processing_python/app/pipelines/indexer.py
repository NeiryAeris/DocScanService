from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.pipelines.chunk import PageText, chunk_pages


class Indexer:
    def __init__(self, gemini_client, qdrant_store, chunk_size: int, overlap: int):
        self.gemini = gemini_client
        self.store = qdrant_store
        self.chunk_size = chunk_size
        self.overlap = overlap

    def upsert_ocr(self, user_id: str, doc_id: str, pages: List[PageText], title: Optional[str] = None) -> Dict[str, Any]:
        chunks = chunk_pages(pages, chunk_size=self.chunk_size, overlap=self.overlap)
        texts = [c["text"] for c in chunks]
        vectors = self.gemini.embed_documents(texts)

        payloads = []
        for c in chunks:
            payloads.append({
                "user_id": user_id,
                "doc_id": doc_id,
                "title": title,
                "page": c["page"],
                "chunk_index": c["chunk_index"],
                "text": c["text"],
            })

        count = self.store.upsert(vectors=vectors, payloads=payloads)
        return {"indexed": True, "chunks": count}
