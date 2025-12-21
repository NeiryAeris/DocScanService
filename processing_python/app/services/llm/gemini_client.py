from __future__ import annotations
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage


class GeminiClient:
    def __init__(self, api_key: str, chat_model: str, embed_model: str):
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")

        self._emb = GoogleGenerativeAIEmbeddings(model=embed_model, google_api_key=api_key)
        self._chat = ChatGoogleGenerativeAI(model=chat_model, google_api_key=api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._emb.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._emb.embed_query(text)

    def generate_text(self, prompt: str) -> str:
        resp = self._chat.invoke([HumanMessage(content=prompt)])
        return getattr(resp, "content", str(resp))
