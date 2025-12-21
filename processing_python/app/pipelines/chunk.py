from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PageText:
    page_number: int
    text: str


def chunk_pages(pages: List[PageText], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    """
    MVP chunking in chars (fast + simple). Later you can switch to token-based.
    Returns list of dict: {page, chunk_index, text}
    """
    out: List[Dict[str, Any]] = []
    for p in pages:
        t = (p.text or "").strip()
        if not t:
            continue

        start = 0
        idx = 0
        while start < len(t):
            end = min(len(t), start + chunk_size)
            piece = t[start:end].strip()
            if piece:
                out.append({"page": p.page_number, "chunk_index": idx, "text": piece})
            idx += 1
            if end == len(t):
                break
            start = max(0, end - overlap)
    return out
