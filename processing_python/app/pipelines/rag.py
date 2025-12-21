from __future__ import annotations

from typing import Any, Dict, List, Optional


class RAG:
    def __init__(self, gemini_client, qdrant_store, top_k: int):
        self.gemini = gemini_client
        self.store = qdrant_store
        self.top_k = top_k

    def ask(self, user_id: str, question: str, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        qv = self.gemini.embed_query(question)
        hits = self.store.search(query_vector=qv, user_id=user_id, doc_ids=doc_ids, top_k=self.top_k)

        ctx = []
        citations = []
        for h in hits:
            p = h.payload or {}
            txt = (p.get("text") or "").strip()
            if not txt:
                continue
            ctx.append(f"[doc:{p.get('doc_id')} page:{p.get('page')}] {txt}")
            citations.append({"doc_id": p.get("doc_id"), "page": p.get("page"), "score": float(getattr(h, "score", 0.0))})

        context_block = "\n\n---\n\n".join(ctx)
        prompt = f"""You are a document Q&A assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say: "I can't find this in your documents."

Context:
{context_block}

Question:
{question}
"""
        answer = self.gemini.generate_text(prompt)
        return {"answer": answer, "citations": citations}
