
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import AlertRule
from .backtest import backtest_equal_weight
from .email_service import send_email
import httpx

def list_rules(db: Session, email: str) -> List[AlertRule]:
    return db.execute(select(AlertRule).where(AlertRule.email==email, AlertRule.active==True)).scalars().all()

def create_rule(db: Session, email: str, data: Dict[str, Any]) -> AlertRule:
    rule = AlertRule(email=email, **data)
    db.add(rule); db.commit(); db.refresh(rule)
    return rule

def delete_rule(db: Session, rule_id: int, email: str) -> bool:
    r = db.get(AlertRule, rule_id)
    if not r or r.email != email: return False
    db.delete(r); db.commit(); return True

async def evaluate_all_rules(db: Session):
    # naive evaluation: run small backtest and notify if alpha exceeds min_alpha
    rules = db.execute(select(AlertRule).where(AlertRule.active==True)).scalars().all()
    if not rules: return
    # Use dummy trades via backtest function for now
    res = backtest_equal_weight([], hold_days=30)
    alpha = res.get("summary",{}).get("alpha", 0)
    sharpe = res.get("summary",{}).get("sharpe", 0)
    for r in rules:
        should = True
        if r.min_alpha is not None and alpha < float(r.min_alpha): should = False
        if r.min_sharpe is not None and sharpe < float(r.min_sharpe): should = False
        if not should: continue
        text = f"Alert '{r.name}': alpha={alpha:.2%}, sharpe={sharpe:.2f} window={r.window_days}"
        if r.delivery.name == "email":
            await send_email(r.email, f"OTP Alert: {r.name}", text)
        elif r.delivery.name == "webhook" and r.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as http:
                    await http.post(r.webhook_url, json={"text": text})
            except Exception:
                pass
