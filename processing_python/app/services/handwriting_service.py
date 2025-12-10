from ..models.handwriting_schema import HandwritingRequest, HandwritingResponse
from ..utils import logger


def remove_handwriting(req: HandwritingRequest) -> HandwritingResponse:
    """
    Dummy handwriting removal: in real life, process image and upload cleaned version.
    """
    logger.info("Running dummy handwriting removal", {"pageId": req.pageId})

    # For now, just pretend cleaned URL is original with a suffix
    clean_url = req.imageUrl + "?cleaned=1"

    return HandwritingResponse(
        jobId=req.jobId,
        status="success",
        cleanImageUrl=clean_url
    )
