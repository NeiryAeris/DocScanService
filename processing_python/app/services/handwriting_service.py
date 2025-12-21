from ..schemas.handwriting import HandwritingRequest, HandwritingResponse
from ..utils import logger

def remove_handwriting(req: HandwritingRequest) -> HandwritingResponse:
    logger.info("Running dummy handwriting removal", {"pageId": req.pageId})
    clean_url = req.imageUrl + "?cleaned=1"
    return HandwritingResponse(jobId=req.jobId, status="success", cleanImageUrl=clean_url)
