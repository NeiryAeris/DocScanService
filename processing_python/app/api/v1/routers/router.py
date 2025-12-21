from fastapi import APIRouter

from .ocr_routes import router as ocr_router
from .handwriting_routes import router as handwriting_router
from .chat_routes import router as chat_router

router = APIRouter()

router.include_router(ocr_router)
router.include_router(handwriting_router)
router.include_router(chat_router)