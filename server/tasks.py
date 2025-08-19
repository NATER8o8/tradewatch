
from typing import Optional, Dict, Any, List
import os
try:
    from rq import Queue, get_current_job
    RQ_OK = True
except Exception:
    RQ_OK = False
from typing import Optional, Dict, Any, List
from .redis_client import get_redis
from .local_queue import QUEUE as LQ, LocalJob
from .db import SessionLocal
from .models import Trade, Official, Brief
from .ai import make_brief
from .slack_integration import respond
from .backtest import backtest_equal_weight


def _use_local_queue() -> bool:
    if not RQ_OK: return True
    if os.environ.get("USE_REDIS", "1") != "1": return True
    try:
        r = get_redis(); r.ping()
        return False
    except Exception:
        return True


def get_queue() -> Queue:
    if _use_local_queue():
        return None  # type: ignore
    return Queue("otp", connection=get_redis())

def _set_progress(pct: int, note: str = ""):
    job = get_current_job() if RQ_OK and not _use_local_queue() else None
    if not job:
        return
    job.meta["progress"] = max(0, min(100, int(pct)))
    if note: job.meta["note"] = str(note)
    job.save_meta()

def brief_task(trade_id: int, response_url: Optional[str] = None) -> dict:
    with SessionLocal() as db:
        tr = db.get(Trade, trade_id)
        if not tr:
            if response_url:
                import asyncio; asyncio.run(respond(response_url, f"Trade {trade_id} not found."))
            return {"ok": False, "error": "not_found"}
        off = db.get(Official, tr.official_id) if tr.official_id else None
        trade_dict = {
            "trade_id": tr.id,
            "official_name": off.name if off else "(unknown)",
            "chamber": off.chamber.value if off else "(unknown)",
            "committee_names": off.committees if off else "",
            "transaction_type": tr.transaction_type.value,
            "owner": tr.owner.value,
            "trade_date": tr.trade_date.isoformat() if tr.trade_date else None,
            "reported_date": tr.reported_date.isoformat() if tr.reported_date else None,
            "ticker": tr.ticker, "issuer": tr.issuer,
            "amount_min": float(tr.amount_min) if tr.amount_min else None,
            "amount_max": float(tr.amount_max) if tr.amount_max else None,
            "filing_url": tr.filing_url,
        }
        _set_progress(10, "Calling AI")
        out = make_brief(trade_dict)
        brief = Brief(trade_id=tr.id, provider="openai", content_md=out.get("text",""), citations=out.get("citations",[]))
        db.add(brief); db.commit(); db.refresh(brief)
        _set_progress(100, "Done")
        msg = f"*Brief for trade #{tr.id}:* {tr.ticker or tr.issuer} — {out.get('text','')[:300]}..."
        if response_url:
            import asyncio; asyncio.run(respond(response_url, msg))
        return {"ok": True, "brief_id": brief.id}

def backtest_task(hold_days: int = 30, benchmark: str = "SPY", chamber: str = None, tx_filter: str = None,
                  start_date=None, end_date=None, sectors: Optional[List[str]] = None, response_url: Optional[str] = None) -> Dict[str, Any]:
    _set_progress(5, "Preparing trades")
    with SessionLocal() as db:
        rows = db.query(Trade, Official).join(Official, Trade.official_id==Official.id, isouter=True).all()
        trades = [{"ticker": t.ticker, "transaction_type": t.transaction_type.value, "trade_date": t.trade_date, "chamber": off.chamber.value if off else None} for t,off in rows]
        _set_progress(30, "Running model")
        res = backtest_equal_weight(trades, hold_days=hold_days, benchmark=benchmark, chamber=chamber, tx_filter=tx_filter, start_date=start_date, end_date=end_date, sectors=sectors)
        _set_progress(90, "Wrapping up")
    _set_progress(100, "Done")
    if response_url:
        import asyncio
        alpha = res.get("summary",{}).get("alpha")
        sharpe = res.get("summary",{}).get("sharpe")
        msg = f"*Backtest* {hold_days}d vs {benchmark}: alpha={alpha:.2%}, sharpe={sharpe:.2f}"
        asyncio.run(respond(response_url, msg))
    return {"ok": True, **res}

def enqueue_brief(trade_id: int, response_url: Optional[str] = None):
    q = get_queue()
    if q is None:
        job = LQ.enqueue(brief_task, trade_id, response_url)
        return {"ok": True, "job_id": job.id}
    job = q.enqueue(brief_task, trade_id, response_url, job_timeout=300)
    return {"ok": True, "job_id": job.get_id()}

def enqueue_backtest(hold_days: int = 30, benchmark: str = "SPY", chamber: str = None, tx_filter: str = None,
                     start_date=None, end_date=None, sectors: Optional[List[str]] = None, response_url: Optional[str] = None):
    q = get_queue()
    if q is None:
        job = LQ.enqueue(backtest_task, hold_days, benchmark, chamber, tx_filter, start_date, end_date, sectors, response_url)
        return {"ok": True, "job_id": job.id}
    job = q.enqueue(backtest_task, hold_days, benchmark, chamber, tx_filter, start_date, end_date, sectors, response_url, job_timeout=600)
    return {"ok": True, "job_id": job.get_id()}
