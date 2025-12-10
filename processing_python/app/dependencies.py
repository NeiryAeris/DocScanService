from fastapi import Header, HTTPException, status
from .config import INTERNAL_TOKEN

async def verify_internal_token(x_internal_token: str = Header(...)):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )