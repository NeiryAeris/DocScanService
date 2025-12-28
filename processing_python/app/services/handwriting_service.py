import os
import httpx

from ..schemas.handwriting import HandwritingRequest, HandwritingResponse
from ..utils import logger

WPI_HW_URL = os.getenv("WPI_HW_URL", "http://wpi_hw:8002/internal/remove-handwriting")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "")

async def remove_handwriting(req: HandwritingRequest) -> HandwritingResponse:
    try:
        logger.info("Handwriting removal proxy -> WPI", {"jobId": req.jobId, "pageId": req.pageId})
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                WPI_HW_URL,
                json=req.dict(),
                headers={"X-Internal-Token": INTERNAL_TOKEN} if INTERNAL_TOKEN else {},
            )
            r.raise_for_status()
            data = r.json()
        return HandwritingResponse(**data)
    except Exception as e:
        logger.error("Handwriting removal failed", {"err": repr(e)})
        return HandwritingResponse(jobId=req.jobId, status="error", error=str(e))
