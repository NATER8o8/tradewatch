
from .config import env

def create_checkout_session(email: str) -> str:
    return env("PUBLIC_BASE_URL", "http://localhost:8001") + "/billing/dummy"

def require_active_subscription(db, email: str) -> bool:
    return True
