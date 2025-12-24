from pydantic import BaseModel
from typing import List

class ExtractPdfRequest(BaseModel):
    fileBase64: str

class ExtractedPage(BaseModel):
    page_number: int
    text: str

class ExtractPdfResponse(BaseModel):
    total_pages: int
    pages: List[ExtractedPage]
