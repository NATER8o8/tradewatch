
import os, json, io, csv, time
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
from rq import Queue
from rq.job import Job

from .db import engine, SessionLocal
from .models import Base, Official, Trade, Brief, Chamber, TxType
from .ai import make_brief
from .billing import create_checkout_session, require_active_subscription
from .scheduler import start_scheduler
from .backtest import backtest_equal_weight
from .config import env
from .security import current_user_email
from .limits import enforce_rate_limit
from .pdf_viewer import _download_to_cache, extract_entities, render_page_with_highlights
from .slack_integration import install_url, oauth_exchange, verify_slack_signature, handle_slash
from .jobs import list_jobs, job_info
from .tasks import enqueue_backtest, get_queue
from .middleware import NoGzipFlagMiddleware
from .auth import require_api_token
from .connectors import fetch_us_senate, fetch_us_house, fetch_uk_register, dedupe
from .ingest import persist_records
from .alerts import list_rules, create_rule, delete_rule
from .metrics_extra import init as init_metrics_extra
from .push import get_vapid_public, set_vapid_keys, add_subscription, send_test_to_all
from .data_quality import quality_report
from .risk import top_officials
from .webhooks import list_dlq, requeue_dlq
from .fts_sqlite import init_sqlite_fts
from .redis_client import get_redis

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Official Trades Pro")

allowed_origins = list({env("FRONTEND_BASE_URL", "http://localhost:3000"), env("PUBLIC_BASE_URL", "http://localhost:8001")})
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(NoGzipFlagMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Prometheus metrics
REGISTRY = CollectorRegistry(auto_describe=True)
REQ_COUNT = Counter("otp_http_requests_total", "HTTP requests total", ["method", "path", "status"], registry=REGISTRY)
REQ_LATENCY = Histogram("otp_http_request_seconds", "HTTP request latency (s)", ["method", "path"], registry=REGISTRY)

@app.middleware("http")
async def metrics_and_rate_limit(request: Request, call_next):
    await enforce_rate_limit(request)
    method = request.method
    path = getattr(request.scope.get('route'), 'path', request.url.path)
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        dur = time.perf_counter() - start
        try:
            REQ_COUNT.labels(method=method, path=path, status=str(status)).inc()
            REQ_LATENCY.labels(method=method, path=path).observe(dur)
        except Exception:
            pass

@app.on_event("startup")
async def on_startup():
    start_scheduler(app)
    init_metrics_extra(REGISTRY)
    init_sqlite_fts()
    # Optionally serve static Next.js export
    if os.environ.get('SERVE_FRONTEND', '0') == '1':
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'webapp', 'out')
        try:
            app.mount('/', StaticFiles(directory=os.path.abspath(static_dir), html=True), name='static')
        except Exception:
            pass

@app.get("/healthz")
def healthz():
    ok = True
    details = {}
    try:
        r = get_redis()
        r.ping()
        details["redis"] = "ok"
    except Exception as e:
        ok = False
        details["redis"] = f"error: {e}"
    try:
        with SessionLocal() as db:
            db.execute(select(func.now()))
        details["db"] = "ok"
    except Exception as e:
        ok = False
        details["db"] = f"error: {e}"
    return {"ok": ok, "components": details}

@app.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse("<h1>Official Trades Pro</h1>")

class CheckoutBody(BaseModel):
    email: str

def db_session():
    with SessionLocal() as db:
        yield db

# --- BILLING ---
@app.post("/api/billing/checkout")
def api_checkout(body: CheckoutBody):
    url = create_checkout_session(body.email)
    return {"ok": True, "url": url}

# --- TRADES ---
@app.get("/api/trades")
def list_trades(
    limit: int = 50,
    offset: int = 0,
    chamber: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    email: Optional[str] = Depends(current_user_email),
    db: Session = Depends(db_session),
):
    require_active_subscription(db, email)
    stmt = select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True)
    conds = []
    if chamber:
        try: conds.append(Official.chamber == Chamber(chamber))
        except Exception: raise HTTPException(status_code=400, detail="Invalid chamber")
    if transaction_type:
        try: conds.append(Trade.transaction_type == TxType(transaction_type))
        except Exception: raise HTTPException(status_code=400, detail="Invalid transaction_type")
    if start_date: conds.append(Trade.trade_date >= start_date)
    if end_date: conds.append(Trade.trade_date <= end_date)
    if conds: stmt = stmt.filter(and_(*conds))
    rows = db.execute(stmt.order_by(Trade.created_at.desc()).limit(limit).offset(offset)).all()
    items = []
    for tr, off in rows:
        items.append({
            "id": tr.id,
            "official_id": tr.official_id,
            "official_name": off.name if off else None,
            "chamber": off.chamber.value if off else None,
            "filing_url": tr.filing_url,
            "trade_date": tr.trade_date.isoformat() if tr.trade_date else None,
            "reported_date": tr.reported_date.isoformat() if tr.reported_date else None,
            "ticker": tr.ticker,
            "issuer": tr.issuer,
            "transaction_type": tr.transaction_type.value,
            "owner": tr.owner.value,
            "amount_min": float(tr.amount_min) if tr.amount_min is not None else None,
            "amount_max": float(tr.amount_max) if tr.amount_max is not None else None,
            "created_at": tr.created_at.isoformat() if tr.created_at else None,
        })
    return {"ok": True, "items": items}

# --- BRIEFS ---
@app.post("/api/brief/latest")
def generate_brief_latest(email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    require_active_subscription(db, email)
    latest = db.execute(select(Trade).order_by(Trade.created_at.desc())).scalars().first()
    if not latest:
        raise HTTPException(status_code=404, detail="No trades")
    off = db.get(Official, latest.official_id) if latest.official_id else None
    trade_dict = {
        "trade_id": latest.id,
        "official_name": off.name if off else "(unknown)",
        "chamber": off.chamber.value if off else "(unknown)",
        "committee_names": off.committees if off else "",
        "transaction_type": latest.transaction_type.value,
        "owner": latest.owner.value,
        "trade_date": latest.trade_date.isoformat() if latest.trade_date else None,
        "reported_date": latest.reported_date.isoformat() if latest.reported_date else None,
        "ticker": latest.ticker, "issuer": latest.issuer,
        "amount_min": float(latest.amount_min) if latest.amount_min else None,
        "amount_max": float(latest.amount_max) if latest.amount_max else None,
        "filing_url": latest.filing_url,
    }
    out = make_brief(trade_dict)
    brief = Brief(trade_id=latest.id, provider="openai", content_md=out.get("text",""), citations=out.get("citations",[]))
    db.add(brief); db.commit(); db.refresh(brief)
    return {"ok": True, "brief_id": brief.id, "content_md": brief.content_md, "citations": brief.citations, "trade_id": latest.id}

@app.post("/api/brief/{trade_id}")
def generate_brief(trade_id: int, email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    require_active_subscription(db, email)
    trade = db.get(Trade, trade_id)
    if not trade: raise HTTPException(status_code=404, detail="Trade not found")
    off = db.get(Official, trade.official_id) if trade.official_id else None
    trade_dict = {
        "trade_id": trade.id,
        "official_name": off.name if off else "(unknown)",
        "chamber": off.chamber.value if off else "(unknown)",
        "committee_names": off.committees if off else "",
        "transaction_type": trade.transaction_type.value,
        "owner": trade.owner.value,
        "trade_date": trade.trade_date.isoformat() if trade.trade_date else None,
        "reported_date": trade.reported_date.isoformat() if trade.reported_date else None,
        "ticker": trade.ticker, "issuer": trade.issuer,
        "amount_min": float(trade.amount_min) if trade.amount_min else None,
        "amount_max": float(trade.amount_max) if trade.amount_max else None,
        "filing_url": trade.filing_url,
    }
    out = make_brief(trade_dict)
    brief = Brief(trade_id=trade.id, provider="openai", content_md=out.get("text",""), citations=out.get("citations",[]))
    db.add(brief); db.commit(); db.refresh(brief)
    return {"ok": True, "brief_id": brief.id, "content_md": brief.content_md, "citations": brief.citations}

# --- BACKTEST (sync) ---
@app.get("/api/backtest")
def api_backtest(
    hold_days: int = Query(30, ge=5, le=365),
    benchmark: str = Query("SPY"),
    chamber: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sectors: Optional[str] = None,
    email: Optional[str] = Depends(current_user_email),
    db: Session = Depends(db_session),
):
    require_active_subscription(db, email)
    rows = db.execute(select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True)).all()
    trades = [{"ticker": t.ticker, "transaction_type": t.transaction_type.value, "trade_date": t.trade_date, "chamber": off.chamber.value if off else None} for t, off in rows]
    sectors_list = [s.strip() for s in sectors.split(",")] if sectors else None
    res = backtest_equal_weight(trades, hold_days=hold_days, benchmark=benchmark, chamber=chamber, tx_filter=transaction_type, start_date=start_date, end_date=end_date, sectors=sectors_list)
    return {"ok": True, **res}

# --- BACKTEST (async job) ---
@app.post("/api/backtest/jobs")
def api_backtest_enqueue(hold_days: int = Query(30, ge=5, le=365), benchmark: str = "SPY"):
    job = enqueue_backtest(hold_days=hold_days, benchmark=benchmark, response_url=None)
    return {"ok": True, **job}

# --- Slack install & events ---
@app.get("/integrations/slack/install")
def slack_install():
    return JSONResponse({"ok": True, "url": install_url()})

@app.get("/integrations/slack/oauth/callback")
async def slack_oauth_callback(code: str):
    data = await oauth_exchange(code)
    if not data.get("ok"):
        raise HTTPException(status_code=400, detail=data.get("error","oauth_failed"))
    return HTMLResponse("<h3>Slack installed. You can close this window.</h3>")

@app.post("/integrations/slack/events")
async def slack_events(request: Request, x_slack_request_timestamp: str = Header(None), x_slack_signature: str = Header(None)):
    body = await request.body()
    if not verify_slack_signature(x_slack_request_timestamp or "", body, x_slack_signature or ""):
        raise HTTPException(status_code=403, detail="invalid signature")
    # Slash command form
    try:
        form = await request.form()
        if "command" in form:
            with SessionLocal() as db:
                await handle_slash(db, dict(form))
            return PlainTextResponse("")
    except Exception:
        pass
    try:
        j = await request.json()
        if j.get("type") == "url_verification":
            return JSONResponse({"challenge": j.get("challenge")})
    except Exception:
        pass
    return PlainTextResponse("ok")

# --- Jobs endpoints ---
@app.get("/api/jobs")
def api_list_jobs(limit: int = 25):
    return {"ok": True, "items": list_jobs(limit=limit)}

@app.get("/api/jobs/{job_id}")
def api_job_detail(job_id: str):
    try:
        info = job_info(job_id)
        return {"ok": True, "item": info}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- CSV EXPORTS ---
@app.get("/api/export/trades.csv")
def export_trades_csv(db: Session = Depends(db_session)):
    rows = db.execute(select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True).order_by(desc(Trade.created_at))).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","trade_date","reported_date","ticker","issuer","transaction_type","owner","amount_min","amount_max","official_name","chamber","filing_url","created_at"])
    for tr, off in rows:
        w.writerow([
            tr.id,
            tr.trade_date.isoformat() if tr.trade_date else "",
            tr.reported_date.isoformat() if tr.reported_date else "",
            tr.ticker or "",
            tr.issuer or "",
            tr.transaction_type.value if tr.transaction_type else "",
            tr.owner.value if tr.owner else "",
            float(tr.amount_min) if tr.amount_min is not None else "",
            float(tr.amount_max) if tr.amount_max is not None else "",
            off.name if off else "",
            off.chamber.value if off and off.chamber else "",
            tr.filing_url or "",
            tr.created_at.isoformat() if tr.created_at else "",
        ])
    data = buf.getvalue()
    headers = {"Content-Disposition": "attachment; filename=trades.csv"}
    return Response(content=data, media_type="text/csv", headers=headers)

@app.get("/api/export/backtest.csv")
def export_backtest_csv(hold_days: int = Query(30, ge=5, le=365), benchmark: str = "SPY", db: Session = Depends(db_session)):
    rows = db.execute(select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True)).all()
    trades = [{"ticker": t.ticker, "transaction_type": t.transaction_type.value, "trade_date": t.trade_date, "chamber": off.chamber.value if off else None} for t, off in rows]
    res = backtest_equal_weight(trades, hold_days=hold_days, benchmark=benchmark)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["section","col1","col2","col3","col4"])
    s = res.get("summary",{})
    w.writerow(["summary","alpha",s.get("alpha",""),"sharpe",s.get("sharpe","")])
    w.writerow(["summary","beta",s.get("beta",""),"idio_vol",s.get("idio_vol","")])
    w.writerow([])
    w.writerow(["top_holdings","ticker","trades","avg_return",""])
    for h in res.get("top_holdings",[]):
        w.writerow(["holding",h.get("ticker",""),h.get("trades",""),h.get("avg_return","")])
    w.writerow([])
    w.writerow(["sector_breakdown","sector","pct","",""])
    for b in res.get("sector_breakdown",[]):
        w.writerow(["sector",b.get("sector",""),b.get("pct",""),"",""])
    data = buf.getvalue()
    headers = {"Content-Disposition": "attachment; filename=backtest.csv"}
    return Response(content=data, media_type="text/csv", headers=headers)

# --- JSON/JSONL EXPORTS ---
@app.get("/api/export/trades.jsonl")
def export_trades_jsonl(db: Session = Depends(db_session)):
    rows = db.execute(select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True).order_by(desc(Trade.created_at))).all()
    out = []
    for tr, off in rows:
        out.append(json.dumps({
            "id": tr.id,
            "trade_date": tr.trade_date.isoformat() if tr.trade_date else None,
            "reported_date": tr.reported_date.isoformat() if tr.reported_date else None,
            "ticker": tr.ticker or None,
            "issuer": tr.issuer or None,
            "transaction_type": tr.transaction_type.value if tr.transaction_type else None,
            "owner": tr.owner.value if tr.owner else None,
            "amount_min": float(tr.amount_min) if tr.amount_min is not None else None,
            "amount_max": float(tr.amount_max) if tr.amount_max is not None else None,
            "official_name": off.name if off else None,
            "chamber": off.chamber.value if off and off.chamber else None,
            "filing_url": tr.filing_url or None,
            "created_at": tr.created_at.isoformat() if tr.created_at else None,
        }))
    data = "\n".join(out) + ("\n" if out else "")
    headers = {"Content-Disposition": "attachment; filename=trades.jsonl"}
    return Response(content=data, media_type="application/x-jsonlines", headers=headers)

@app.get("/api/export/backtest.json")
def export_backtest_json(hold_days: int = Query(30, ge=5, le=365), benchmark: str = "SPY", db: Session = Depends(db_session)):
    rows = db.execute(select(Trade, Official).join(Official, Trade.official_id == Official.id, isouter=True)).all()
    trades = [{"ticker": t.ticker, "transaction_type": t.transaction_type.value, "trade_date": t.trade_date, "chamber": off.chamber.value if off else None} for t, off in rows]
    res = backtest_equal_weight(trades, hold_days=hold_days, benchmark=benchmark)
    headers = {"Content-Disposition": "attachment; filename=backtest.json"}
    return JSONResponse(content=res, headers=headers)

# --- Admin: Jobs management & connectors ---
@app.post("/api/admin/jobs/retry/{job_id}")
def admin_retry_job(job_id: str, ok: bool = Depends(require_api_token)):
    q = get_queue()
    job = Job.fetch(job_id, connection=q.connection)
    job.requeue()
    return {"ok": True, "job_id": job_id}

@app.post("/api/admin/jobs/requeue_failed")
def admin_requeue_failed(ok: bool = Depends(require_api_token)):
    q = get_queue()
    from rq.registry import FailedJobRegistry
    reg = FailedJobRegistry(queue=q)
    for jid in reg.get_job_ids():
        Job.fetch(jid, connection=q.connection).requeue()
    return {"ok": True}

@app.post("/api/admin/ingest/run")
def admin_ingest_run(source: str = Query("us-senate"), persist: int = Query(1)):
    if source == "us-senate":
        recs = fetch_us_senate()
    elif source == "us-house":
        recs = fetch_us_house()
    elif source == "uk":
        recs = fetch_uk_register()
    else:
        raise HTTPException(status_code=400, detail="unknown source")
    out = dedupe(recs)
    added = 0
    if persist:
        with SessionLocal() as db:
            added = persist_records(db, out)
    return {"ok": True, "count": len(out), "added": added, "items": out[:25]}

# --- Alerts CRUD ---
class AlertIn(BaseModel):
    name: str
    min_alpha: float | None = None
    min_sharpe: float | None = None
    sector_pct_threshold: float | None = None
    window_days: int = 30
    sectors: str = ""
    frequency: str = "daily"
    delivery: str = "email"
    webhook_url: str | None = None

@app.get("/api/alerts/rules")
def api_list_rules(email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    rules = list_rules(db, email or "demo@example.com")
    items = [{
        "id": r.id, "name": r.name, "min_alpha": float(r.min_alpha) if r.min_alpha is not None else None,
        "min_sharpe": float(r.min_sharpe) if r.min_sharpe is not None else None, "window_days": r.window_days,
        "sectors": r.sectors, "frequency": r.frequency.value, "delivery": r.delivery.value, "webhook_url": r.webhook_url
    } for r in rules]
    return {"ok": True, "items": items}

@app.post("/api/alerts/rules")
def api_create_rule(body: AlertIn, email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    rule = create_rule(db, email or "demo@example.com", {
        "name": body.name, "min_alpha": body.min_alpha, "min_sharpe": body.min_sharpe,
        "sector_pct_threshold": body.sector_pct_threshold, "window_days": body.window_days,
        "sectors": body.sectors, "frequency": body.frequency, "delivery": body.delivery, "webhook_url": body.webhook_url
    })
    return {"ok": True, "id": rule.id}

@app.delete("/api/alerts/rules/{rule_id}")
def api_delete_rule(rule_id: int, email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    ok = delete_rule(db, rule_id, email or "demo@example.com")
    return {"ok": ok}

@app.post("/api/admin/ingest/run_all")
def admin_ingest_run_all(persist: int = Query(1), limit: int = Query(0)):
    recs = []
    if limit and limit > 0:
        recs += fetch_us_house(limit=limit)
        recs += fetch_us_senate(limit=limit)
        recs += fetch_uk_register(limit=limit)
    else:
        recs += fetch_us_house()
        recs += fetch_us_senate()
        recs += fetch_uk_register()
    uniq = dedupe(recs)
    added = 0
    if persist:
        with SessionLocal() as db:
            added = persist_records(db, uniq)
    return {"ok": True, "fetched": len(recs), "unique": len(uniq), "added": added}

from sqlalchemy import text
@app.get("/api/search")
def api_search(q: str, limit: int = 25):
    with engine.connect() as conn:
        try:
            rows = conn.execute(text("SELECT rowid FROM trades_fts WHERE trades_fts MATCH :q LIMIT :lim"), {"q": q, "lim": limit}).fetchall()
            ids = [r[0] for r in rows]
        except Exception:
            ids = []
    with SessionLocal() as db:
        results = []
        if ids:
            for tid in ids:
                tr = db.get(Trade, tid)
                off = db.get(Official, tr.official_id) if tr else None
                if tr:
                    results.append({
                        "id": tr.id,
                        "ticker": tr.ticker, "issuer": tr.issuer, "transaction_type": tr.transaction_type.value if tr.transaction_type else None,
                        "owner": tr.owner.value if tr.owner else None, "official_name": off.name if off else None, "chamber": off.chamber.value if off else None,
                        "trade_date": tr.trade_date.isoformat() if tr.trade_date else None, "reported_date": tr.reported_date.isoformat() if tr.reported_date else None
                    })
        return {"ok": True, "items": results}

class InitBody(BaseModel):
    api_token: str | None = None


@app.post("/api/admin/init")
def api_init(body: InitBody, db: Session = Depends(db_session)):
    token = body.api_token or ""
    if not token:
        # generate a strong default
        import secrets
        token = secrets.token_urlsafe(32)
    from .models import Setting
    row = db.query(Setting).filter(Setting.key=="api_token").first()
    if row:
        row.value = token
    else:
        db.add(Setting(key="api_token", value=token))
    db.commit()
    return {"ok": True, "api_token": token}


@app.post("/api/export/save")
def export_to_sdcard(fmt: str = Query("csv")):
    # Determine path
    base = "/sdcard/Download"
    os.makedirs(base, exist_ok=True)
    if fmt == "csv":
        r = export_trades_csv()  # type: ignore
        path = os.path.join(base, "official-trades.csv")
        with open(path, "wb") as f: f.write(r.body if hasattr(r, "body") else (r if isinstance(r, bytes) else str(r).encode()))
        return {"ok": True, "path": path}
    elif fmt == "jsonl":
        r = export_trades_jsonl()  # type: ignore
        path = os.path.join(base, "official-trades.jsonl")
        with open(path, "wb") as f: f.write(r.body if hasattr(r, "body") else (r if isinstance(r, bytes) else str(r).encode()))
        return {"ok": True, "path": path}
    else:
        raise HTTPException(status_code=400, detail="fmt must be csv|jsonl")

@app.get("/api/trades/{trade_id}/sources")
def api_trade_sources(trade_id: int, db: Session = Depends(db_session)):
    from .models import TradeSource
    rows = db.query(TradeSource).filter(TradeSource.trade_id==trade_id).all()
    items = [{"id": r.id, "source": r.source, "source_url": r.source_url, "retrieved_at": str(r.retrieved_at), "raw_json": r.raw_json} for r in rows]
    return {"ok": True, "items": items}

# Push: VAPID public key
@app.get("/api/push/public_key")
def api_push_pubkey(db: Session = Depends(db_session)):
    return {"ok": True, "public_key": get_vapid_public(db)}

# Push: register subscription
class PushBody(BaseModel):
    endpoint: str
    keys: dict

@app.post("/api/push/register")
def api_push_register(body: PushBody, email: Optional[str] = Depends(current_user_email), db: Session = Depends(db_session)):
    sid = add_subscription(db, email or "", body.dict())
    return {"ok": True, "id": sid}

# Push: test broadcast
@app.post("/api/push/test")
def api_push_test(db: Session = Depends(db_session)):
    sent = send_test_to_all(db, text="Test alert: subscriptions connected")
    return {"ok": True, "sent": sent}

# Quality report
@app.get("/api/admin/quality/report")
def api_quality_report(db: Session = Depends(db_session)):
    return {"ok": True, **quality_report(db)}

@app.get("/api/admin/webhooks/dlq")
def api_webhook_dlq():
    return {"ok": True, "items": list_dlq()}

@app.post("/api/admin/webhooks/requeue")
def api_webhook_requeue(max_items: int = 50):
    n = requeue_dlq(max_items=max_items)
    return {"ok": True, "requeued": n}

@app.get("/api/risk/officials")
def api_risk_officials(limit: int = 50, db: Session = Depends(db_session)):
    items = top_officials(db, limit=limit)
    # attach names
    out = []
    for it in items:
        off = db.get(Official, it["official_id"])
        out.append({**it, "official_name": (off.name if off else None)})
    return {"ok": True, "items": out}
