import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException

_hits: dict = defaultdict(list)
_lock = threading.Lock()

RATE_LIMIT = 30   # max requests
WINDOW_SEC = 60   # per minute


def rate_limit_check(ip: str):
    now = time.time()
    with _lock:
        hits = _hits[ip]
        # Remove old hits outside window
        _hits[ip] = [t for t in hits if now - t < WINDOW_SEC]
        if len(_hits[ip]) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
        _hits[ip].append(now)


async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    # Only rate-limit extraction start
    if request.url.path == "/api/start-extraction":
        rate_limit_check(ip)
    return await call_next(request)
