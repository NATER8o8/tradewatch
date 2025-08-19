
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import Trade, Official
from .linking import infer_sector_from_committees

# NOTE: This is a heuristic score (0..100). It's not a legal conclusion.
# Features:
# - Trade frequency (last 12m)
# - Committee-sector overlap heuristic
# - Average (placeholder) alpha per trade (no external prices -> proxy using buy>sell imbalance)
# - Recency boost

def _safe(v, d=0.0):
    try: return float(v)
    except Exception: return d

def score_official(db: Session, official_id: int) -> Dict[str, Any]:
    now = date.today()
    start = now - timedelta(days=365)
    trades: List[Trade] = db.query(Trade).filter(Trade.official_id==official_id, Trade.trade_date >= start).all()
    freq = len(trades)
    # committee-sector overlap
    off: Official = db.get(Official, official_id)
    sector = infer_sector_from_committees(off.committees or "") if off else None
    overlap = 0
    if sector:
        for t in trades:
            issuer = (t.issuer or "").lower()
            tick = (t.ticker or "").lower()
            if sector in ["energy"] and any(k in issuer for k in ["oil","gas","energy"]): overlap += 1
            if sector in ["healthcare"] and any(k in issuer for k in ["pharma","bio","health"]): overlap += 1
            if sector in ["technology"] and any(k in issuer for k in ["tech","ai","chip","semiconductor","software"]): overlap += 1
            if sector in ["finance"] and any(k in issuer for k in ["bank","financial","capital","broker"]): overlap += 1
    # alpha proxy: buys count +1, sells -0.5 (placeholder without price data)
    alpha_proxy = sum(1.0 if (t.transaction_type.name if hasattr(t.transaction_type,'name') else str(t.transaction_type)).lower().startswith("buy") else -0.5 for t in trades)
    recency = 0
    for t in trades:
        if t.trade_date and (now - t.trade_date).days <= 30:
            recency += 1
    # Normalize into score (0..100)
    s = 0.0
    s += min(freq / 20.0, 1.0) * 40.0
    s += min(overlap / 5.0, 1.0) * 30.0
    s += min(max(alpha_proxy, 0.0) / 10.0, 1.0) * 20.0
    s += min(recency / 5.0, 1.0) * 10.0
    return {"official_id": official_id, "score": round(s, 1), "freq": freq, "overlap": overlap, "alpha_proxy": alpha_proxy, "recency": recency, "sector": sector}

def top_officials(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    ids = [x[0] for x in db.query(Official.id).all()]
    scores = [score_official(db, oid) for oid in ids]
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]
