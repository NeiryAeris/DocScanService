# app/api/v1/routers/handwriting_routes.py
from fastapi import APIRouter, Depends
from ....core.deps import verify_internal_token
from ....schemas.handwriting import HandwritingRequest, HandwritingResponse
from ....services.handwriting_service import remove_handwriting

router = APIRouter(
    prefix='/internal',
    tags=['handwriting'],
    dependencies=[Depends(verify_internal_token)]
)

@router.post('/remove-handwriting', response_model=HandwritingResponse)
async def remove_handwriting_endpoint(req: HandwritingRequest) -> HandwritingResponse:
    return await remove_handwriting(req)
