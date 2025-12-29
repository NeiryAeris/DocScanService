import os
import uuid
import base64
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from remove_handwriting import main as remove_hw_main

app = FastAPI(title="WPI Handwriting Removal", version="0.1.0")

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "")
WORK_ROOT = Path("/tmp/wpi_hw").resolve()

class HandwritingOptions(BaseModel):
    strength: str = "medium"  # low|medium|high

class HandwritingRequest(BaseModel):
    jobId: str
    pageId: str
    imageUrl: Optional[str] = None
    imageBase64: Optional[str] = None
    options: HandwritingOptions = HandwritingOptions()

class HandwritingResponse(BaseModel):
    jobId: str
    status: str
    cleanImageUrl: Optional[str] = None
    error: Optional[str] = None

def _auth(x_internal_token: Optional[str]):
    if INTERNAL_TOKEN and x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid X-Internal-Token")

def _strip_data_url_prefix(b64: str) -> str:
    if not b64:
        return b64
    head = b64[:80].lower()
    if "base64" in head and "," in b64:
        return b64.split(",", 1)[1]
    return b64

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/internal/remove-handwriting", response_model=HandwritingResponse)
async def remove_handwriting(
    req: HandwritingRequest,
    x_internal_token: Optional[str] = Header(default=None, alias="X-Internal-Token"),
):
    _auth(x_internal_token)

    job = req.jobId or uuid.uuid4().hex
    job_dir = WORK_ROOT / job
    in_dir = job_dir / "in"
    out_dir = job_dir / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # get input bytes: base64 preferred, fallback to imageUrl
    img_bytes: Optional[bytes] = None

    if req.imageBase64:
        try:
            b64 = _strip_data_url_prefix(req.imageBase64)
            img_bytes = base64.b64decode(b64, validate=False)
        except Exception as e:
            return HandwritingResponse(jobId=job, status="error", error=f"Invalid base64: {e}")

    if img_bytes is None:
        if not req.imageUrl:
            return HandwritingResponse(jobId=job, status="error", error="No imageBase64 or imageUrl provided")
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.get(req.imageUrl)
                r.raise_for_status()
                img_bytes = r.content
        except Exception as e:
            return HandwritingResponse(jobId=job, status="error", error=f"Download failed: {e}")

    # save as input.png
    in_path = in_dir / "input.png"
    in_path.write_bytes(img_bytes)

    strength = (req.options.strength or "medium").lower().strip()
    use_mean = True if strength == "low" else False  # low = faster/worse

    # run WPI
    try:
        class Args:
            input_dir = Path(in_dir)
            output_dir = Path(out_dir)
            image_mean_method = use_mean

        remove_hw_main(args=Args())
    except Exception as e:
        return HandwritingResponse(jobId=job, status="error", error=f"WPI failed: {e}")

    outs = [p for p in out_dir.glob("*") if p.is_file()]
    if not outs:
        return HandwritingResponse(jobId=job, status="error", error="No output produced")

    outs = sorted(outs, key=lambda p: ("mask" in p.name.lower(), -p.stat().st_size))
    out_path = outs[0]
    data = out_path.read_bytes()

    b64 = base64.b64encode(data).decode("utf-8")
    mime = "image/png" if out_path.suffix.lower() == ".png" else "image/jpeg"
    return HandwritingResponse(jobId=job, status="success", cleanImageUrl=f"data:{mime};base64,{b64}")
