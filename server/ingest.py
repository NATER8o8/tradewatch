
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from dateutil import parser as dateparser

from .models import Official, Trade, Chamber, TxType, Owner, TradeSource
import json
from . import storage_s3

def parse_amount_range(txt: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not txt: return (None, None)
    s = txt.replace("$","").replace(",","").strip()
    parts = [p.strip() for p in s.split("-")]
    if len(parts) == 2:
        try:
            lo = float(parts[0])
            hi = float(parts[1])
            return (lo, hi)
        except Exception:
            return (None, None)
    try:
        v = float(s)
        return (v, v)
    except Exception:
        return (None, None)

def parse_date(txt: Optional[str]) -> Optional[date]:
    if not txt: return None
    try:
        return dateparser.parse(txt, dayfirst=False).date()
    except Exception:
        return None

def upsert_official(db: Session, name: str, chamber: str, state: Optional[str] = None) -> Official:
    ch = Chamber(chamber) if isinstance(chamber, str) else chamber
    row = db.execute(select(Official).where(and_(Official.name==name, Official.chamber==ch))).scalars().first()
    if row: return row
    off = Official(name=name, chamber=ch, state=state or "")
    db.add(off); db.commit(); db.refresh(off)
    return off

def trade_exists(db: Session, official_id: int, trade_date: Optional[date], ticker: Optional[str], issuer: Optional[str], tx_type: TxType) -> bool:
    stmt = select(Trade).where(and_(
        Trade.official_id==official_id,
        Trade.trade_date==trade_date,
        Trade.ticker==(ticker or ""),
        Trade.issuer==(issuer or ""),
        Trade.transaction_type==tx_type
    )).limit(1)
    return db.execute(stmt).first() is not None

def persist_records(db: Session, records: List[Dict[str, Any]], source_url: str | None = None) -> int:
    """
    Records keys: official_name, chamber ('house'|'senate'|'other'), ticker|issuer, transaction_type ('buy'|'sell'|...),
    owner, amount, amount_min, amount_max, trade_date, reported_date, filing_url
    """
    added = 0
    for r in records:
        name = (r.get("official_name") or "").strip()
        chamber = (r.get("chamber") or "other").strip()
        if not name:
            name = "Unknown"
        off = upsert_official(db, name, chamber, r.get("state"))
        tx_str = (r.get("transaction_type") or "unknown").lower()
        try:
            tx = TxType(tx_str) if tx_str in TxType.__members__ else TxType[tx_str]  # allow enum name
        except Exception:
            tx = TxType.buy if "buy" in tx_str else (TxType.sell if "sell" in tx_str else TxType.unknown)
        own_str = (r.get("owner") or "unknown").lower()
        try:
            owner = Owner[own_str] if own_str in Owner.__members__ else Owner.unknown
        except Exception:
            owner = Owner.unknown
        trade_date = r.get("trade_date")
        if isinstance(trade_date, str):
            trade_date = parse_date(trade_date)
        reported_date = r.get("reported_date")
        if isinstance(reported_date, str):
            reported_date = parse_date(reported_date)
        amount_min, amount_max = r.get("amount_min"), r.get("amount_max")
        if (amount_min, amount_max) == (None, None) and r.get("amount"):
            amount_min, amount_max = parse_amount_range(r.get("amount"))
        ticker = r.get("ticker") or ""
        issuer = r.get("issuer") or ""
        if trade_exists(db, off.id, trade_date, ticker, issuer, tx):
            continue
        tr = Trade(
            official_id=off.id,
            filing_url=r.get("filing_url") or "",
            transaction_type=tx,
            owner=owner,
            trade_date=trade_date,
            reported_date=reported_date,
            ticker=ticker,
            issuer=issuer,
            amount_min=amount_min,
            amount_max=amount_max
        )
        db.add(tr); db.flush(); added += 1
        # provenance snapshot
        try:
            src = TradeSource(trade_id=tr.id, source=(r.get('source') or ''), source_url=(r.get('source_url') or source_url or ''), raw_json=json.dumps(r))
            try:
                s3k = storage_s3.put_json(r, key_hint='trade')
                if s3k:
                    src.raw_json = json.dumps({"local": r, "s3_key": s3k})
            except Exception:
                pass
            db.add(src)
        except Exception:
            pass
    db.commit()
    return added
