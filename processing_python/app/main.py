from fastapi import FastAPI
from .api.v1.routers import ocr_router, handwriting_router, qa_router
from .core.config import PYTHON_SERVICE_PORT
from .utils import logger

import os
import platform
import shutil
import subprocess
from typing import Optional, Dict, Any

app = FastAPI(
    title="Document Processing Service",
    version="0.1.0"
)

# Routers
app.include_router(ocr_router.router)
app.include_router(handwriting_router.router)
app.include_router(qa_router.router)


# -----------------------------
# Tesseract configuration + checks
# -----------------------------

def _default_tesseract_cmd() -> str:
    if platform.system().lower().startswith("win"):
        return r"D:\Tesseract\Tesseract-OCR\tesseract.exe"
    return "tesseract"


def _resolve_tesseract_cmd() -> str:
    """
    Resolve tesseract command using:
      1) env var TESSERACT_CMD
      2) default OS path
      3) shutil.which('tesseract')
    """
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd:
        return env_cmd

    default_cmd = _default_tesseract_cmd()
    # If default_cmd is a file path, keep it if exists
    if os.path.sep in default_cmd or default_cmd.endswith(".exe"):
        if os.path.exists(default_cmd):
            return default_cmd

    # Try PATH
    which = shutil.which("tesseract")
    if which:
        return which

    # Fallback to default (may fail; we’ll report in health)
    return default_cmd


def _inject_tesseract_into_path(tesseract_cmd: str) -> None:
    """
    If tesseract_cmd is an absolute path to an executable, prepend its directory to PATH.
    This helps subprocess calls that use 'tesseract' and some libraries.
    """
    if os.path.exists(tesseract_cmd):
        exe_dir = os.path.dirname(os.path.abspath(tesseract_cmd))
        current = os.environ.get("PATH", "")
        if exe_dir and exe_dir not in current:
            os.environ["PATH"] = exe_dir + os.pathsep + current


def check_tesseract(tesseract_cmd: str) -> Dict[str, Any]:
    """
    Run a fast diagnostic for:
      - command resolution (exists / which)
      - running `tesseract --version`
      - TESSDATA_PREFIX presence (optional but common issue)
    """
    info: Dict[str, Any] = {
        "tesseract_cmd": tesseract_cmd,
        "platform": platform.platform(),
        "which_tesseract": shutil.which("tesseract"),
        "path_head": os.environ.get("PATH", "")[:2000],  # avoid huge logs
        "tessdata_prefix": os.getenv("TESSDATA_PREFIX"),
        "ok": False,
        "version_output": None,
        "error": None,
    }

    # If user gave a path, verify it exists
    if (os.path.sep in tesseract_cmd or tesseract_cmd.endswith(".exe")) and not os.path.exists(tesseract_cmd):
        info["error"] = f"Tesseract executable not found at: {tesseract_cmd}"
        return info

    try:
        out = subprocess.check_output([tesseract_cmd, "--version"], stderr=subprocess.STDOUT)
        info["version_output"] = out.decode(errors="replace").strip()
        info["ok"] = True
    except Exception as e:
        info["error"] = f"Failed to run '{tesseract_cmd} --version': {repr(e)}"

    return info


# Store latest check results in-memory for easy inspection
TESSERACT_CMD = _resolve_tesseract_cmd()
_inject_tesseract_into_path(TESSERACT_CMD)
TESSERACT_STATUS = check_tesseract(TESSERACT_CMD)

if TESSERACT_STATUS["ok"]:
    logger.info("✅ Tesseract check OK")
    logger.info(f"Using TESSERACT_CMD={TESSERACT_CMD}")
else:
    logger.error("❌ Tesseract check FAILED")
    logger.error(f"Using TESSERACT_CMD={TESSERACT_CMD}")
    logger.error(f"Reason: {TESSERACT_STATUS['error']}")


# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def root():
    return {"message": "Document Processing Service is running."}


@app.get("/health")
def health_check():
    # Basic health
    return {"status": "healthy"}


@app.get("/health/tesseract")
def health_tesseract():
    """
    Detailed diagnostic endpoint to see what the service process can access.
    Useful on Windows + Docker.
    """
    # Refresh each time in case env changes or container differs
    cmd = _resolve_tesseract_cmd()
    _inject_tesseract_into_path(cmd)
    status = check_tesseract(cmd)
    return status


# Optional: expose what command your OCR router should use
# so you can import it there: from .main import TESSERACT_CMD
# (If circular imports happen, move this into a shared config module.)
@app.get("/debug/tesseract-cmd")
def debug_tesseract_cmd():
    return {"TESSERACT_CMD": TESSERACT_CMD}


def start():
    logger.info(f"Starting DocScan Processing Service on port {PYTHON_SERVICE_PORT}")
