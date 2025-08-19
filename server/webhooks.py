
import json, time, os, asyncio
from typing import Dict, Any, Optional
import httpx
from .redis_client import get_redis

DLQ_KEY = "otp:webhook:dlq"
OUTBOX_KEY = "otp:webhook:outbox"

async def send_webhook(url: str, payload: Dict[str, Any], retries: int = 3, backoff: float = 1.0) -> bool:
    for i in range(retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                r = await http.post(url, json=payload)
                if r.status_code // 100 == 2:
                    return True
        except Exception:
            pass
        await asyncio.sleep(backoff * (2 ** i))
    # push to DLQ
    try:
        r = get_redis()
        r.lpush(DLQ_KEY, json.dumps({"url": url, "payload": payload, "ts": time.time()}))
    except Exception:
        pass
    return False

def list_dlq(max_items: int = 50):
    try:
        r = get_redis()
        items = r.lrange(DLQ_KEY, 0, max_items-1)
        return [json.loads(x) for x in items]
    except Exception:
        return []

def requeue_dlq(max_items: int = 50):
    try:
        r = get_redis()
        items = r.lrange(DLQ_KEY, 0, max_items-1)
        for x in items:
            r.rpush(OUTBOX_KEY, x)  # back to outbox
        r.ltrim(DLQ_KEY, max_items, -1)
        return len(items)
    except Exception:
        return 0
