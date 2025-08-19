
from fastapi import Request
from .redis_client import get_redis
from .rbac import get_plan
from .security import current_user_email

async def enforce_rate_limit(request: Request):
    try:
        r = get_redis()
        ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{ip}:{request.url.path}"
        val = r.incr(key)
        if val == 1:
            r.expire(key, 60)
    except Exception:
        pass
