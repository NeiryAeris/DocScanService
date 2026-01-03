# app/services/llm/gemini_client.py
from __future__ import annotations

from typing import List, Optional

from google import genai
from google.genai import types


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        embed_model: str,
        chat_model: Optional[str] = None,
        embed_dims: Optional[int] = None,  # optional: reduce vector size (e.g., 768/1536)
        max_output_tokens: int = 1024,
        temperature: float = 0.2,
    ):
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")

        self._client = genai.Client(api_key=api_key)
        self._embed_model = embed_model
        self._chat_model = chat_model
        self._embed_dims = embed_dims
        self._max_output_tokens = int(max_output_tokens or 1024)
        self._temperature = float(temperature if temperature is not None else 0.2)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        cfg = types.EmbedContentConfig(output_dimensionality=self._embed_dims) if self._embed_dims else None

        BATCH = 100  # Google GenAI limit
        out: List[List[float]] = []

        for start in range(0, len(texts), BATCH):
            batch = texts[start : start + BATCH]

            resp = self._client.models.embed_content(
                model=self._embed_model,
                contents=batch,
                config=cfg,
            )

            embs: List[List[float]] = []
            for e in resp.embeddings:
                values = getattr(e, "values", e)
                embs.append(list(values))

            if len(embs) != len(batch):
                raise RuntimeError(f"Embedding count mismatch: got {len(embs)} for {len(batch)} texts")

            out.extend(embs)

        if len(out) != len(texts):
            raise RuntimeError(f"Embedding count mismatch: got {len(out)} for {len(texts)} texts")

        return out

    def embed_query(self, text: str) -> List[float]:
        vecs = self.embed_documents([text])
        return vecs[0] if vecs else []

    def generate_text(self, prompt: str) -> str:
        if not self._chat_model:
            raise RuntimeError("Chat model not configured (set GEMINI_CHAT_MODEL).")

        resp = self._client.models.generate_content(
            model=self._chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
            ),
        )
        return resp.text or ""
