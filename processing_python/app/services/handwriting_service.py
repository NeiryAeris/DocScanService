# app/services/handwriting_service.py
import os

from ..schemas.handwriting import HandwritingRequest, HandwritingResponse
from ..utils import logger
from .handwriting_engine.pipeline import HandwritingRemovalPipeline

_PIPELINE: HandwritingRemovalPipeline | None = None

def _get_pipeline() -> HandwritingRemovalPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        device = os.getenv("HW_DEVICE", "cpu")
        seg_ckpt = os.getenv("HW_SEGMENTER_CKPT", "")
        inpaint = os.getenv("HW_INPAINT_WEIGHTS", "")
        patch = int(os.getenv("HW_PATCH_SIZE", "256"))
        overlap = int(os.getenv("HW_OVERLAP", "32"))
        hw_class = int(os.getenv("HW_HANDWRITING_CLASS", "2"))

        if not seg_ckpt or not inpaint:
            raise RuntimeError("Missing HW_SEGMENTER_CKPT or HW_INPAINT_WEIGHTS env vars")

        _PIPELINE = HandwritingRemovalPipeline(
            device=device,
            seg_ckpt=seg_ckpt,
            inpaint_weights=inpaint,
            patch_size=patch,
            overlap=overlap,
            handwriting_class=hw_class
        )
    return _PIPELINE

async def remove_handwriting(req: HandwritingRequest) -> HandwritingResponse:
    try:
        logger.info("Handwriting removal start", {"pageId": req.pageId, "jobId": req.jobId})
        pipe = _get_pipeline()
        data_url = await pipe.run_to_data_url(req.imageUrl)
        return HandwritingResponse(jobId=req.jobId, status="success", cleanImageUrl=data_url)
    except Exception as e:
        logger.error("Handwriting removal failed", {"err": repr(e)})
        return HandwritingResponse(jobId=req.jobId, status="error", error=str(e))
