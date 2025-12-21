from fastapi import APIRouter, Depends
from ..dependencies import verify_internal_token
from ..models.handwriting_schema import HandwritingRequest, HandwritingResponse
from ..services.handwriting_service import remove_handwriting

router = APIRouter(
    prefix='/internal',
    tags=['handwriting'],
    dependencies=[Depends(verify_internal_token)]
)

@router.post('/remove-handwriting', response_model=HandwritingResponse)
def remove_handwriting_endpoint(req: HandwritingRequest) -> HandwritingResponse:
    """
    Internal endpoint to remove handwriting from a given image URL.
    """
    return remove_handwriting(req)
