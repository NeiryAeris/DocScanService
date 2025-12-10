from fastapi import APIRouter, Depends
from ..dependencies import verify_internal_token
from ..models.qa_schema import QaRequest, QaResponse
from ..services.qa_service import answer_question

router = APIRouter(
    prefix="/internal",
    tags=["qa"],
    dependencies=[Depends(verify_internal_token)]
)


@router.post("/qa/answer", response_model=QaResponse)
def qa_answer_endpoint(body: QaRequest):
    return answer_question(body)
