# app/services/ocr_service.py
import base64
import io
from PIL import Image
from ..models.ocr_schema import OcrRequest, OcrResponse
from ..utils import logger
from .ocr_pipline import run_ocr_image_bytes, run_ocr_image_base64

def run_ocr(req: OcrRequest) -> OcrResponse:
    """
    This is what /internal/ocr calls.

    Uses the OCR pipeline built from your CLI text logic.
    """
    try:
        if not req.imageBase64:
            return OcrResponse(
                jobId=req.jobId,
                status="error",
                text="",
                language="",
                confidence=0.0,
                layout=None,
                error="No imageBase64 provided",
            )

        languages = req.options.languages or ["vie", "eng"]

        result = run_ocr_image_base64(req.imageBase64, languages)

        # TODO: compute real confidence from boxes if you want
        return OcrResponse(
            jobId=req.jobId,
            status="success",
            text=result["text"],
            language=result["language"],
            confidence=0.99,
            layout={
                "tokens": result["tokens"],
                "tokenPositions": result["tokenPositions"],
                "boxes": result["boxes"],
            },
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in run_ocr: {e}")
        return OcrResponse(
            jobId=req.jobId,
            status="error",
            text="",
            language="",
            confidence=0.0,
            layout=None,
            error=str(e),
        )
