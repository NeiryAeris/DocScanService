# app/services/ocr_service.py
from ..models.ocr_schema import OcrRequest, OcrResponse
from ..utils import logger


def run_ocr(req: OcrRequest) -> OcrResponse:
    """
    Dummy OCR: in real life, download image from req.imageUrl and run OCR engine.
    """
    logger.info("Running dummy OCR", {"pageId": req.pageId, "imageUrl": req.imageUrl})

    fake_text = f"[DUMMY OCR] This is placeholder text for page {req.pageId}."
    layout = None
    if req.options.returnLayout:
        layout = {
            "blocks": [
                {
                    "bbox": [0, 0, 100, 30],
                    "text": fake_text,
                    "lines": []
                }
            ]
        }

    return OcrResponse(
        jobId=req.jobId,
        status="success",
        text=fake_text,
        language=req.options.languages[0] if req.options.languages else "en",
        confidence=0.99,
        layout=layout
    )
