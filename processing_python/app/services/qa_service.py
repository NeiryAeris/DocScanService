from ..models.qa_schema import QaRequest, QaResponse, QaSource
from ..utils import logger


def answer_question(req: QaRequest) -> QaResponse:
    """
    Dummy QA: just echo question and pick first page as source.
    """
    logger.info("Running dummy QA", {"docId": req.docId, "question": req.question})

    if not req.pages:
        return QaResponse(
            docId=req.docId,
            answer="I could not find any content in this document.",
            sources=[],
            status="error",
            error="No pages provided"
        )

    # naive "source"
    first_page = req.pages[0]
    answer = f"[DUMMY ANSWER] You asked: '{req.question}'. This is a placeholder answer based on page {first_page.pageId}."

    sources = [
        QaSource(
            pageId=first_page.pageId,
            text=first_page.text[:200],
            score=0.5
        )
    ]

    return QaResponse(
        docId=req.docId,
        answer=answer,
        sources=sources,
        status="success"
    )
