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
    cleanImageUrl: Optional[str] = None
    error: Optional[str] = None