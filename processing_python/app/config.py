import os
from dotenv import load_dotenv

load_dotenv()

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is missing.")
    return value

PYTHON_SERVICE_PORT: int = int(os.getenv("PYTHON_SERVICE_PORT", "8001"))

INTERNAL_TOKEN: str = required("INTERNAL_TOKEN")