
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import Trade, Official

def quality_report(db: Session) -> Dict[str, Any]:
    res: Dict[str, Any] = {"summary": {}, "issues": []}
    # Missing key fields
    missing_ticker = db.query(Trade).filter((Trade.ticker==None) | (Trade.ticker=="")).count()
    missing_issuer = db.query(Trade).filter((Trade.issuer==None) | (Trade.issuer=="")).count()
    total = db.query(Trade).count()
    res["summary"] = {"total_trades": total, "missing_ticker": missing_ticker, "missing_issuer": missing_issuer}
    # Contradictions: reported before trade
    bad_dates = db.execute(select(Trade.id, Trade.trade_date, Trade.reported_date).where(Trade.reported_date != None, Trade.trade_date != None, Trade.reported_date < Trade.trade_date)).all()
    for tid, td, rd in bad_dates:
        res["issues"].append({"type":"date_order", "trade_id": tid, "trade_date": str(td), "reported_date": str(rd)})
    # Outlier amounts (very large)
    big = db.execute(select(Trade.id, Trade.amount_max).where(Trade.amount_max != None, Trade.amount_max > 50_000_000)).all()
    for tid, amt in big:
        res["issues"].append({"type":"amount_outlier", "trade_id": tid, "amount_max": float(amt)})
    return res
