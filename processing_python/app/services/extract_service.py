from __future__ import annotations

import base64
import binascii
from io import BytesIO

from pypdf import PdfReader

from app.schemas.extract import ExtractPdfResponse, ExtractedPage


def _clean_b64(s: str) -> str:
    s = (s or "").strip()
    # allow data URLs
    if s.startswith("data:"):
        comma = s.find(",")
        if comma != -1:
            s = s[comma + 1 :]
    return s


def extract_pdf_text_pages(fileBase64: str) -> ExtractPdfResponse:
    b64 = _clean_b64(fileBase64)
    if not b64:
        return ExtractPdfResponse(total_pages=0, pages=[])

    try:
        pdf_bytes = base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Invalid base64 PDF payload: {e}") from e

    reader = PdfReader(BytesIO(pdf_bytes))

    pages: list[ExtractedPage] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(ExtractedPage(page_number=i, text=text))

    return ExtractPdfResponse(total_pages=len(pages), pages=pages)
