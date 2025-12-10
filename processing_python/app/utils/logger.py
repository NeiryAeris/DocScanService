from datetime import datetime

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def info(msg: str, meta=None) -> None: 
    print(f"[INFO] [{_ts()}] {msg}", meta or "")
    
def error(msg: str, meta=None) -> None:
    print(f"[ERROR] [{_ts()}] {msg}", meta or "")