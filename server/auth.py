
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from .config import env
from .db import SessionLocal
from .models import Setting

def _db_token(db: Session) -> str:
    s = db.query(Setting).filter(Setting.key=="api_token").first()
    return s.value if s else ""

def require_api_token(authorization: str = Header(default=""), db: Session = Depends(lambda: SessionLocal())):
    expected = env("API_TOKEN", "") or _db_token(db)
    if not expected:
        return True  # no token set yet
    token = authorization.split(" ", 1)[1] if authorization.lower().startswith("bearer ") and " " in authorization else authorization
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return True
