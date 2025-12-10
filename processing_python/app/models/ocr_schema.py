from pydantic import BaseModel
from typing import List, Optional, Any

class OcrOptions(BaseModel):
    languages: List[str] = "en"
    returnLayout: bool = True
    
class OcrRequest(BaseModel):
    """
    Internal OCR request payload.

    - jobId:   internal job identifier (from Node)
    - pageId:  page identifier (from Node)
    - imageBase64: base64-encoded image data (preferred in current flow)
    - imageUrl:    optional URL to image (for future S3/MinIO usage)
    - options:     OCR options (languages, layout)
    """
    jobId: str
    pageId: str
    imageUrl: Optional[str] = None
    imageBase64: Optional[str] = None
    options: OcrOptions = OcrOptions()
    
class LayoutBlock(BaseModel):
    """
    Placeholder structure for layout blocks.
    You can extend this later with more detailed structure.
    """
    # id: str
    # type: str
    boundingBox: Optional[list[int]] = None
    text: str
    # confidence: Optional[float] = None
    # additionalData: Optional[Any] = None
    lines: Optional[list[Any]] = None  # simplify for now
    
class OcrResponse(BaseModel):
    """
    OCR response returned to Node.

    - status:     "success" or "error"
    - text:       recognized text (empty if error)
    - language:   main language detected/used
    - confidence: dummy value for now, can be tied to engine later
    - layout:     optional layout data (blocks, lines)
    - error:      error message if status == "error"
    """
    jobId: str
    status: str
    text: str
    language: str
    confidence: float
    layout: Optional[dict] = None
    error: Optional[str] = None