# app/services/llm/gemini_client.py
from __future__ import annotations
from typing import List, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None


class GeminiClient:
    def __init__(self, api_key: str, embed_model: str, chat_model: Optional[str] = None):
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")

        self._emb = GoogleGenerativeAIEmbeddings(model=embed_model, google_api_key=api_key)
        self._chat = None

        # Only initialize chat if you actually provide a model name
        if chat_model:
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError("ChatGoogleGenerativeAI not available. Install langchain-google-genai.")
            self._chat = ChatGoogleGenerativeAI(model=chat_model, google_api_key=api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._emb.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._emb.embed_query(text)

    def generate_text(self, prompt: str) -> str:
        if not self._chat:
            raise RuntimeError("Chat model not configured (set GEMINI_CHAT_MODEL).")
        resp = self._chat.invoke([HumanMessage(content=prompt)])
        return getattr(resp, "content", str(resp))
