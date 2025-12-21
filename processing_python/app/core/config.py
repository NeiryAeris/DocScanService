import os
from dotenv import load_dotenv

load_dotenv()

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is missing.")
    return value

PYTHON_SERVICE_PORT: int = int(os.getenv("PYTHON_SERVICE_PORT", "8001"))

ENV: str = os.getenv("ENV", "dev")
_token = os.getenv("INTERNAL_TOKEN")

if not _token:
    if ENV.lower() in ("prod", "production"):
        INTERNAL_TOKEN: str = required("INTERNAL_TOKEN")
    else:
        INTERNAL_TOKEN = "dev-internal-token"
        print("[WARN] INTERNAL_TOKEN not set; using dev-internal-token")
else:
    INTERNAL_TOKEN = _token
    
    
# Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL: str = os.getenv("GEMINI_EMBED_MODEL","")

# Qdrant
QDRANT_URL: str = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")  # optional
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "doc_chunks")

# RAG knobs
TOP_K: int = int(os.getenv("TOP_K", "8"))
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1200"))       # chars (simple MVP)
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))  # chars