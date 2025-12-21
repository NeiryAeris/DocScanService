from pydantic import BaseModel
from typing import Optional

class HandwritingOptions(BaseModel):
    strength: str = 'medium'
    
class HandwritingRequest(BaseModel):
    jobId: str
    pageId: str
    imageUrl: str
    options: HandwritingOptions = HandwritingOptions()
    
class HandwritingResponse(BaseModel):
    jobId: str
    status: str
    text: str
    confidence: float
    error: Optional[str] = None