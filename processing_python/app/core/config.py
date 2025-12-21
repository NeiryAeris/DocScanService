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