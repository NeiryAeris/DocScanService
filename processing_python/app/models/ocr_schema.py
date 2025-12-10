from pydantic import BaseModel
from typing import List, Optional, Any

class OcrOptions(BaseModel):
    language: List[str] = "en"
    returnLayout: bool = True
    
class OcrRequest(BaseModel):
    jobId: str
    pageId: str
    imageUrl: str
    options: OcrOptions = OcrOptions()
    
class LayoutBlock(BaseModel):
    # id: str
    # type: str
    boundingBox: Optional[list[int]] = None
    text: str
    # confidence: Optional[float] = None
    # additionalData: Optional[Any] = None
    lines: Optional[list[Any]] = None  # simplify for now
    
class OcrResponse(BaseModel):
    jobId: str
    status: str
    text: str
    language: str
    confidence: float
    layout: Optional[dict] = None
    error: Optional[str] = None