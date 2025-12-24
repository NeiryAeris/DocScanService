from fastapi import APIRouter, Depends
from app.core.deps import verify_internal_token
from app.schemas.extract import ExtractPdfRequest, ExtractPdfResponse
from app.services.extract_service import extract_pdf_text_pages

router = APIRouter(
    prefix="/internal/extract",
    tags=["extract"],
    dependencies=[Depends(verify_internal_token)],
)

@router.post("/pdf", response_model=ExtractPdfResponse)
def extract_pdf(body: ExtractPdfRequest) -> ExtractPdfResponse:
    return extract_pdf_text_pages(body.fileBase64)
