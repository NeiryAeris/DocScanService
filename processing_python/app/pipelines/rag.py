# app/pipelines/rag.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


class RAG:
    def __init__(self, gemini_client, qdrant_store, top_k: int):
        self.gemini = gemini_client
        self.store = qdrant_store
        self.top_k = top_k

    def ask(self, user_id: str, question: str, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        # 1) embed query
        qv = self.gemini.embed_query(question)

        # 2) retrieve
        hits = self.store.search(
            query_vector=qv,
            user_id=user_id,
            doc_ids=doc_ids,
            top_k=self.top_k,
        )

        contexts: List[str] = []
        citations: List[Dict[str, Any]] = []

        for h in hits:
            p = h.payload or {}
            txt = (p.get("text") or "").strip()
            if not txt:
                continue

            doc_id = p.get("doc_id")
            page = p.get("page")
            chunk_index = p.get("chunk_index")

            contexts.append(f"[doc:{doc_id} page:{page} chunk:{chunk_index}]\n{txt}")
            citations.append({
                "doc_id": doc_id,
                "page": page,
                "chunk_index": chunk_index,
                "score": float(getattr(h, "score", 0.0)),
            })

        if not contexts:
            return {
                "answer": "I can't find this in your documents.",
                "citations": [],
                "used_chunks": 0,
            }

        context_block = "\n\n---\n\n".join(contexts)

        # 3) generate answer (ONLY from context)
        prompt = f"""You are a document Q&A assistant.

Rules:
- Answer ONLY using the provided context.
- If the answer is not in the context, say: "I can't find this in your documents."
- Cite sources inline like: (doc_id, page)

Context:
{context_block}

Question:
{question}
"""

        answer = self.gemini.generate_text(prompt)
        return {"answer": answer, "citations": citations, "used_chunks": len(contexts)}
