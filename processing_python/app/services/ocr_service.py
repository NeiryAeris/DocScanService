# app/services/ocr_service.py
import base64
import io
from PIL import Image
from ..models.ocr_schema import OcrRequest, OcrResponse


def run_ocr(req: OcrRequest) -> OcrResponse:
    if req.imageBase64:
        image_bytes = base64.b64decode(req.imageBase64)
        image = Image.open(io.BytesIO(image_bytes))
        # TODO: feed into OCR engine
    else:
        # fallback: use imageUrl (future)
        image = None

    fake_text = f"[DUMMY OCR] Processed page {req.pageId}"
    return OcrResponse(
        jobId=req.jobId,
        status="success",
        text=fake_text,
        language=req.options.languages[0],
        confidence=0.98,
        layout=None
    )
