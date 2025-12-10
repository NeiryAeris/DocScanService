# app/services/ocr_service.py
import base64
import io
from PIL import Image
from ..models.ocr_schema import OcrRequest, OcrResponse
from ..utils import logger

def run_ocr(req: OcrRequest) -> OcrResponse:
    """
    Dummy OCR implementation for smoke testing.

    Current behaviour:
    - If imageBase64 is present, validate it as base64 (do NOT actually OCR yet).
    - If imageUrl is present (future use), just log it.
    - Always return a fake OCR text on success.
    - On any exception, return status="error" and do NOT crash FastAPI.

    This is intentionally simple so the full pipeline
    Android -> Node -> Python works reliably.
    Later you can plug in real OCR engine here.
    """
    try:
        # --- handle image data (just validate base64 for now) ---
        if req.imageBase64:
            # Validate base64 (will throw if invalid)
            decoded = base64.b64decode(req.imageBase64, validate=True)
            logger.info(
                "Received base64 image for OCR",
                {"pageId": req.pageId, "bytes": len(decoded)},
            )
        elif req.imageUrl:
            # Future: download from URL and OCR
            logger.info(
                "Received imageUrl for OCR (not used yet)",
                {"pageId": req.pageId, "url": req.imageUrl},
            )
        else:
            logger.info("No image data provided for OCR", {"pageId": req.pageId})

        # --- choose language robustly ---
        chosen_lang = "en"
        opts = req.options

        if getattr(opts, "languages", None):
            # if it's a list and not empty
            langs = opts.languages or []
            if isinstance(langs, list) and len(langs) > 0:
                chosen_lang = langs[0]
        elif getattr(opts, "language", None):
            chosen_lang = opts.language or "en"

        fake_text = f"[DUMMY OCR] Processed page {req.pageId}"

        return OcrResponse(
            jobId=req.jobId,
            status="success",
            text=fake_text,
            language=chosen_lang,
            confidence=0.99,
            layout=None,
            error=None,
        )

    except Exception as e:
        # Catch all exceptions so FastAPI doesn't return 500 to Node
        logger.error("Error in run_ocr", {"error": str(e), "jobId": req.jobId})
        return OcrResponse(
            jobId=req.jobId,
            status="error",
            text="",
            language="",
            confidence=0.0,
            layout=None,
            error=str(e),
        )
