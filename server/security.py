
from typing import Optional
from fastapi import Request

async def current_user_email(request: Request) -> Optional[str]:
    return request.headers.get("X-Demo-Email", "demo@example.com")
