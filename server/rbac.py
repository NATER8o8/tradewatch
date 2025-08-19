
from typing import Optional
from sqlalchemy.orm import Session
from .models import Setting

DEFAULT_PLAN = {
    "export_limit": 10000,
    "api_rate_per_min": 120,
    "alerts_per_user": 5,
}

PLANS = {
    "free": {"export_limit": 1000, "api_rate_per_min": 60, "alerts_per_user": 1},
    "pro": {"export_limit": 25000, "api_rate_per_min": 600, "alerts_per_user": 20},
    "enterprise": {"export_limit": 100000, "api_rate_per_min": 2000, "alerts_per_user": 100},
}

def get_plan(db: Session, email: Optional[str]) -> dict:
    if not email:
        return DEFAULT_PLAN
    row = db.query(Setting).filter(Setting.key==f"plan:{email}").first()
    if not row:
        return DEFAULT_PLAN
    return PLANS.get(row.value, DEFAULT_PLAN)
