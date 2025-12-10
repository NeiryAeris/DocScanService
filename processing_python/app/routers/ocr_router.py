from fastapi import APIRouter, Depends
from ..dependencies import verify_internal_token
from ..models.ocr_schema import OcrRequest, OcrResponse
from ..services.ocr_service import run_ocr

router = APIRouter(
    prefix='/internal',
    tags=['ocr'],
    dependencies=[Depends(verify_internal_token)]
)

@router.post('/ocr', response_model=OcrResponse)
def ocr_endpoint(req: OcrRequest) -> OcrResponse:
    """
    Internal endpoint to run OCR on a given image URL.
    """
    return run_ocr(req)