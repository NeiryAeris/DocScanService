from pydantic import BaseModel
from typing import Optional

class HandwritingOptions(BaseModel):
    strength: str = "medium"  # low|medium|high

class HandwritingRequest(BaseModel):
    jobId: str
    pageId: str

    # Prefer base64 in your current flow (same as OCR)
    imageBase64: Optional[str] = None

    # Still allow URL (future / alternative)
    imageUrl: Optional[str] = None

    options: HandwritingOptions = HandwritingOptions()

class HandwritingResponse(BaseModel):
    jobId: str
    status: str
    cleanImageUrl: Optional[str] = None
    error: Optional[str] = None
