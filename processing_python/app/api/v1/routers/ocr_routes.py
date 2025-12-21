from fastapi import APIRouter, Depends

from ....core.deps import verify_internal_token
from ....schemas.ocr import OcrRequest, OcrResponse
from ....services.ocr_service import run_ocr

router = APIRouter(
    prefix='/internal',
    tags=['ocr'],
    dependencies=[Depends(verify_internal_token)]
)

@router.post('/ocr', response_model=OcrResponse)
def ocr_endpoint(body: OcrRequest) -> OcrResponse:
    """
    Internal OCR endpoint, called only by the Node.js gateway.

    Expected payload (from Node):

    {
      "jobId": "job_test-page-1",
      "pageId": "test-page-1",
      "imageBase64": "...",          # base64 of uploaded image
      "imageUrl": null,              # optional, future
      "options": {
        "languages": ["vi", "en"],
        "returnLayout": true
      }
    }
    """
    return run_ocr(body)