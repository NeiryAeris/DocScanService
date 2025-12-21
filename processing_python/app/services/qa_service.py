from __future__ import annotations

from ..schemas.chat import QaRequest, QaResponse, QaSource
from ..utils import logger

def answer_question(req: QaRequest) -> QaResponse:
    logger.info("Running dummy QA", {"jobId": req.jobId, "question": req.question})

    if not req.pages:
        return QaResponse(
            jobId=req.jobId,
            status="error",
            answer="I can't find this in your documents.",
            confidence=0.0,
            sources=[],
            error="No pages provided",
        )

    first_page = req.pages[0]
    snippet = (first_page.content or "")[:200]
    answer = f"[DUMMY ANSWER] You asked: '{req.question}'. Placeholder cites page {first_page.pageId}."

    sources = [QaSource(pageId=str(first_page.pageId), text=snippet, score=0.5)]
    return QaResponse(jobId=req.jobId, status="success", answer=answer, confidence=0.5, sources=sources)
