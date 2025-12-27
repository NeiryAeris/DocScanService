"""DocScan Processing Service (FastAPI).

This file makes `app` a proper Python package, improving import stability across
different runtimes (local, Docker, CI).
"""

__all__ = ["main"]