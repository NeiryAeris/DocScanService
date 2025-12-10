from fastapi import FastAPI
from .routers import ocr_router, handwriting_router, qa_router
from .config import PYTHON_SERVICE_PORT
from .utils import logger

app = FastAPI(
    title="Document Processing Service",
    version="0.1.0"
)


# Routers
app.include_router(ocr_router.router)
app.include_router(handwriting_router.router)
app.include_router(qa_router.router)

@app.get("/")
def root():
    return {"message": "Document Processing Service is running."}

def start():
    logger.info(f"Starting DocScan Processing Service on port {PYTHON_SERVICE_PORT}")