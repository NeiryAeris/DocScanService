# app/services/ocr_service.py

import base64
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional, Tuple, Union

from ..schemas.ocr import OcrRequest, OcrResponse
from ..utils import logger


# -----------------------------
# Helpers
# -----------------------------

def _strip_data_url_prefix(b64: str) -> str:
    """
    Handle base64 that comes as:
      "data:image/png;base64,AAAA..."
    """
    if not b64:
        return b64
    head = b64[:80].lower()
    if "base64" in head and "," in b64:
        return b64.split(",", 1)[1]
    return b64


def _detect_image_suffix(image_bytes: bytes) -> str:
    """
    Best-effort file suffix for tesseract input.
    (We avoid Pillow; this is purely header-based.)
    """
    if not image_bytes:
        return ".img"

    # PNG
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    # JPEG
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    # GIF
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return ".gif"
    # BMP
    if image_bytes.startswith(b"BM"):
        return ".bmp"
    # TIFF
    if image_bytes.startswith(b"II*\x00") or image_bytes.startswith(b"MM\x00*"):
        return ".tif"

    return ".img"


def _resolve_tesseract_cmd() -> str:
    """
    Resolve tesseract command using:
      1) env var TESSERACT_CMD (optional override)
      2) PATH via shutil.which
      3) fallback to "tesseract" (subprocess will raise a clear error)
    """
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd:
        return env_cmd

    which = shutil.which("tesseract")
    if which:
        return which

    return "tesseract"


def _ensure_tesseract_available(cmd: str) -> None:
    """
    Provide a clean error when tesseract isn't installed / reachable.
    """
    # If cmd is a path, check existence
    if (os.path.sep in cmd or cmd.lower().endswith(".exe")) and not os.path.exists(cmd):
        raise RuntimeError(
            f"Tesseract executable not found at '{cmd}'. "
            f"Install tesseract or set TESSERACT_CMD to the correct path."
        )

    # If cmd is "tesseract" but not in PATH
    if cmd == "tesseract" and shutil.which("tesseract") is None and not os.getenv("TESSERACT_CMD"):
        raise RuntimeError(
            "Tesseract not found on PATH. "
            "Install it (Docker: apt-get install tesseract-ocr + language packs) "
            "or set TESSERACT_CMD to the executable path."
        )


def _map_lang_to_tesseract(langs: Union[List[str], str, None]) -> Tuple[str, str]:
    """
    Input can be:
      - ["vi","en"] (from Node)
      - ["vie","eng"] (tesseract traineddata names)
      - "vi" or "en" (if schema default is currently a string)
    Output:
      - ("vie+eng", "vi")   # (tesseract lang string, primary language as provided)
    """
    if langs is None:
        return ("eng", "en")

    # If someone passed a string (your current schema default does that)
    if isinstance(langs, str):
        langs_list = [langs]
    else:
        langs_list = list(langs)

    cleaned: List[str] = []
    primary_raw = (langs_list[0] or "en").strip().lower() if langs_list else "en"

    for l in langs_list:
        l = (l or "").strip().lower()
        if not l:
            continue

        # Node-style -> tesseract traineddata codes
        if l in ("en", "eng", "english"):
            cleaned.append("eng")
        elif l in ("vi", "vie", "vietnamese"):
            cleaned.append("vie")
        else:
            # allow raw traineddata code passthrough (e.g. "deu", "jpn")
            cleaned.append(l)

    # de-dupe while preserving order
    uniq: List[str] = []
    for x in cleaned:
        if x not in uniq:
            uniq.append(x)

    tess_lang = "+".join(uniq) if uniq else "eng"
    return (tess_lang, primary_raw)


def _run_tesseract_text(image_bytes: bytes, lang: str, psm: int, oem: int) -> str:
    """
    Run the tesseract CLI and return stdout text.
    """
    cmd = _resolve_tesseract_cmd()
    _ensure_tesseract_available(cmd)

    suffix = _detect_image_suffix(image_bytes)
    tmp_path: Optional[str] = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            tmp_path = f.name
            f.write(image_bytes)

        args = [
            cmd,
            tmp_path,
            "stdout",
            "-l",
            lang,
            "--psm",
            str(psm),
            "--oem",
            str(oem),
        ]

        logger.info("Running tesseract OCR", {"cmd": args, "bytes": len(image_bytes)})

        out = subprocess.check_output(args, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")

    except subprocess.CalledProcessError as e:
        # Include tesseract stdout/stderr for debugging (language pack missing etc.)
        msg = e.output.decode("utf-8", errors="replace") if e.output else repr(e)
        raise RuntimeError(f"Tesseract failed: {msg}") from e

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# -----------------------------
# Main entrypoint (router calls this)
# -----------------------------

def run_ocr(req: OcrRequest) -> OcrResponse:
    """
    Text-only OCR via Tesseract.

    - No preprocessing (you do it on-device already).
    - Currently supports imageBase64 (preferred).
    - imageUrl intentionally not implemented yet.
    """
    try:
        if not req.imageBase64 and not req.imageUrl:
            return OcrResponse(
                jobId=req.jobId,
                status="error",
                text="",
                language="",
                confidence=0.0,
                layout=None,
                error="No imageBase64 or imageUrl provided",
            )

        if req.imageUrl and not req.imageBase64:
            return OcrResponse(
                jobId=req.jobId,
                status="error",
                text="",
                language="",
                confidence=0.0,
                layout=None,
                error="imageUrl not supported yet. Send imageBase64 instead.",
            )

        # Decode base64
        b64 = _strip_data_url_prefix(req.imageBase64 or "")
        try:
            image_bytes = base64.b64decode(b64, validate=False)
        except Exception as e:
            return OcrResponse(
                jobId=req.jobId,
                status="error",
                text="",
                language="",
                confidence=0.0,
                layout=None,
                error=f"Invalid base64 image: {str(e)}",
            )

        # Options
        opts = req.options
        langs = getattr(opts, "languages", None)
        tess_lang, primary_lang = _map_lang_to_tesseract(langs)

        # Optional (if you later add these fields to schema)
        psm = int(getattr(opts, "psm", 6) or 6)
        oem = int(getattr(opts, "oem", 1) or 1)

        text = _run_tesseract_text(image_bytes, lang=tess_lang, psm=psm, oem=oem).strip()

        return OcrResponse(
            jobId=req.jobId,
            status="success",
            text=text,
            language=primary_lang,
            confidence=1.0,   # global confidence not trivial from tesseract; keep a placeholder
            layout=None,      # text-only for now
            error=None,
        )

    except Exception as e:
        logger.error("Error in run_ocr", {"error": str(e), "jobId": req.jobId})
        return OcrResponse(
            jobId=req.jobId,
            status="error",
            text="",
            language="",
            confidence=0.0,
            layout=None,
            error=str(e),
        )
