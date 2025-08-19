
from typing import Dict, Any, List, Optional
import json
from sqlalchemy.orm import Session
from .models import Setting, PushSubscription
from .db import SessionLocal
from .config import env

def get_vapid_public(db: Session) -> str:
    v = db.query(Setting).filter(Setting.key=="vapid_public").first()
    return v.value if v else (env("VAPID_PUBLIC_KEY", "") or "")

def get_vapid_private(db: Session) -> str:
    v = db.query(Setting).filter(Setting.key=="vapid_private").first()
    return v.value if v else (env("VAPID_PRIVATE_KEY", "") or "")

def set_vapid_keys(db: Session, public: str, private: str):
    row = db.query(Setting).filter(Setting.key=="vapid_public").first()
    if row: row.value = public
    else: db.add(Setting(key="vapid_public", value=public))
    row2 = db.query(Setting).filter(Setting.key=="vapid_private").first()
    if row2: row2.value = private
    else: db.add(Setting(key="vapid_private", value=private))
    db.commit()

def list_subscriptions(db: Session, email: Optional[str]=None) -> List[PushSubscription]:
    q = db.query(PushSubscription)
    if email: q = q.filter(PushSubscription.email==email)
    return q.all()

def add_subscription(db: Session, email: str, sub: Dict[str, Any]) -> int:
    endpoint = sub.get("endpoint","")
    keys = sub.get("keys", {})
    row = PushSubscription(email=email or "", endpoint=endpoint, p256dh=keys.get("p256dh",""), auth=keys.get("auth",""))
    db.add(row); db.commit(); db.refresh(row)
    return row.id

def send_test_to_all(db: Session, text: str = "Hello from OTP") -> int:
    # Lazy import to keep optional
    try:
        from pywebpush import webpush, WebPushException
    except Exception:
        return 0
    pub = get_vapid_public(db)
    priv = get_vapid_private(db)
    if not pub or not priv:
        return 0
    subs = list_subscriptions(db)
    count = 0
    for s in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": s.endpoint,
                    "keys": {"p256dh": s.p256dh, "auth": s.auth},
                },
                data=json.dumps({"title": "Official Trades Pro", "body": text}),
                vapid_private_key=priv,
                vapid_claims={"sub": "mailto:admin@example.com"},
                vapid_public_key=pub,
            )
            count += 1
        except Exception:
            pass
    return count
