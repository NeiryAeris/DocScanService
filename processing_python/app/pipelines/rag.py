# app/pipelines/rag.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal


ChatMode = Literal["auto", "doc", "general"]


class RAG:
    def __init__(
        self,
        gemini_client,
        qdrant_store,
        top_k: int,
        min_score: float = 0.0,
        general_system_prompt: str = "You are a helpful assistant.",
    ):
        self.gemini = gemini_client
        self.store = qdrant_store
        self.top_k = top_k
        self.min_score = float(min_score or 0.0)
        self.general_system_prompt = general_system_prompt or "You are a helpful assistant."

    def _build_general_prompt(
        self,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        # Stateless chat: we format history into a single prompt.
        # Keep it short to avoid token blowups.
        max_turns = 20
        turns = (history or [])[-max_turns:]

        lines: List[str] = []
        lines.append(self.general_system_prompt.strip())
        lines.append("")  # spacer

        for m in turns:
            role = (m.get("role") or "user").lower()
            text = m.get("text") or m.get("content") or ""
            text = str(text).strip()
            if not text:
                continue

            if role == "assistant":
                lines.append(f"Assistant: {text}")
            elif role == "system":
                lines.append(f"System: {text}")
            else:
                lines.append(f"User: {text}")

        lines.append(f"User: {question}")
        lines.append("Assistant:")
        return "\n".join(lines)

    def ask(
        self,
        user_id: str,
        question: str,
        doc_ids: Optional[List[str]] = None,
        mode: ChatMode = "auto",
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # If forced general mode: skip vector search entirely.
        if mode == "general":
            prompt = self._build_general_prompt(question=question, history=history)
            answer = self.gemini.generate_text(prompt)
            return {
                "answer": answer,
                "citations": [],
                "used_chunks": 0,
                "mode_used": "general",
            }

        # 1) embed query
        qv = self.gemini.embed_query(question)

        # 2) retrieve
        hits = self.store.search(
            query_vector=qv,
            user_id=user_id,
            doc_ids=doc_ids,
            top_k=self.top_k,
        )

        # Optional score gating (treat weak matches as "no docs")
        if hits and self.min_score > 0.0:
            hits = [h for h in hits if float(getattr(h, "score", 0.0)) >= self.min_score]

        contexts: List[str] = []
        citations: List[Dict[str, Any]] = []

        for h in hits or []:
            p = getattr(h, "payload", {}) or {}
            txt = p.get("text") or ""
            if not txt:
                continue

            doc_id = p.get("doc_id")
            page = p.get("page")
            chunk_index = p.get("chunk_index")

            contexts.append(f"[doc:{doc_id} page:{page} chunk:{chunk_index}]\n{txt}")
            citations.append(
                {
                    "doc_id": doc_id,
                    "page": page,
                    "chunk_index": chunk_index,
                    "score": float(getattr(h, "score", 0.0)),
                }
            )

        # If no doc context:
        if not contexts:
            # If forced doc mode, keep old behavior
            if mode == "doc":
                return {
                    "answer": "I can't find this in your documents.",
                    "citations": [],
                    "used_chunks": 0,
                    "mode_used": "doc",
                }

            # AUTO fallback => generic conversation
            prompt = self._build_general_prompt(question=question, history=history)
            answer = self.gemini.generate_text(prompt)
            return {
                "answer": answer,
                "citations": [],
                "used_chunks": 0,
                "mode_used": "general",
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
        return {
            "answer": answer,
            "citations": citations,
            "used_chunks": len(contexts),
            "mode_used": "doc",
        }
