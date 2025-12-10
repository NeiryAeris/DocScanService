from pydantic import BaseModel, Field
from typing import List, Optional

class Qapage(BaseModel):
    pageId: int
    content: str
    
class QaOptions(BaseModel):
    maxTokens: int = 256
    confidenceThreshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
class QaRequest(BaseModel):
    jobId: str
    question: str
    pages: List[Qapage]
    options: QaOptions = QaOptions()
    
class QaSource(BaseModel):
    pageId: str
    text: str
    score: float
    
class QaResponse(BaseModel):
    jobId: str
    status: str
    answer: str
    confidence: float
    sources: List[QaSource] = []
    error: Optional[str] = None