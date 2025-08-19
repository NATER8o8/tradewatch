
import hmac, hashlib, time, re
from typing import Dict, Any
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from .config import env
from .tasks import enqueue_brief, enqueue_backtest
from .models import Trade, Official

SLACK_CLIENT_ID = env("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = env("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET = env("SLACK_SIGNING_SECRET", "")
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", "http://localhost:8001")

SCOPES = ["commands","chat:write","app_mentions:read"]

def install_url() -> str:
    params = {"client_id": SLACK_CLIENT_ID, "scope": " ".join(SCOPES), "redirect_uri": f"{PUBLIC_BASE_URL}/integrations/slack/oauth/callback"}
    return "https://slack.com/oauth/v2/authorize?" + urlencode(params)

async def oauth_exchange(code: str):
    async with httpx.AsyncClient(timeout=10.0) as http:
        r = await http.post("https://slack.com/api/oauth.v2.access", data={
            "client_id": SLACK_CLIENT_ID, "client_secret": SLACK_CLIENT_SECRET, "code": code, "redirect_uri": f"{PUBLIC_BASE_URL}/integrations/slack/oauth/callback"
        })
        return r.json()

def verify_slack_signature(timestamp: str, body: bytes, signature: str) -> bool:
    if not SLACK_SIGNING_SECRET:
        return True
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 60*5:
            return False
    except Exception:
        return False
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    mac = hmac.new(SLACK_SIGNING_SECRET.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()
    expected = f"v0={mac}"
    return hmac.compare_digest(expected, signature or "")

async def respond(response_url: str, text: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            await http.post(response_url, json={"text": text})
    except Exception:
        pass

async def handle_slash(db: Session, payload: Dict[str, Any]):
    text = (payload.get("text") or "").strip()
    response_url = payload.get("response_url")

    def latest_trade_id() -> int:
        row = db.execute(select(Trade).order_by(desc(Trade.created_at))).scalars().first()
        return row.id if row else 0

    if text.startswith("latest"):
        parts = text.split()
        n = 5
        if len(parts) > 1:
            try: n = int(parts[1])
            except: pass
        rows = db.execute(select(Trade, Official).join(Official, Trade.official_id==Official.id, isouter=True).order_by(desc(Trade.created_at)).limit(n)).all()
        lines = ["*Latest trades:*"]
        for tr, off in rows:
            who = off.name if off else "Unknown"
            what = tr.ticker or tr.issuer or "(unknown)"
            lines.append(f"- {tr.trade_date}: {tr.transaction_type.value.upper()} {what} by {who} (#{tr.id})")
        await respond(response_url, "\n".join(lines) if lines else "No trades.")
    elif text.startswith("backtest"):
        parts = text.split()
        hold = 30
        if len(parts) > 1:
            try: hold = int(parts[1])
            except: pass
        job = enqueue_backtest(hold_days=hold, response_url=response_url)
        await respond(response_url, f"Backtest queued (hold_days={hold}). Job: `{job['job_id']}`")
    elif text.startswith("brief"):
        if "latest" in text or text.strip() == "brief":
            tid = latest_trade_id()
            if not tid:
                await respond(response_url, "No trades found.")
                return
            job = enqueue_brief(tid, response_url=response_url)
            await respond(response_url, f"Generating brief for latest trade #{tid}… job `{job['job_id']}`")
            return
        m = re.search(r"brief\s+(\d+)", text)
        if m:
            trade_id = int(m.group(1))
            job = enqueue_brief(trade_id, response_url=response_url)
            await respond(response_url, f"Generating brief for trade #{trade_id}… job `{job['job_id']}`")
        else:
            await respond(response_url, "Usage: `/otp brief {trade_id}` or `/otp brief latest`")
    elif text.startswith("digest"):
        parts = text.split()
        n = 5
        for p in parts[1:]:
            try:
                n = int(p)
                break
            except:
                pass
        rows = db.execute(select(Trade, Official).join(Official, Trade.official_id==Official.id, isouter=True).order_by(desc(Trade.created_at)).limit(n)).all()
        if not rows:
            await respond(response_url, "No recent trades to include in digest.")
            return
        lines = [f"*Official Trades Digest — Top {len(rows)}*"]
        for tr, off in rows:
            who = off.name if off else "Unknown"
            what = tr.ticker or tr.issuer or "(unknown)"
            when = tr.trade_date or tr.reported_date
            lines.append(f"• {when}: {tr.transaction_type.value.upper()} {what} by {who} (#{tr.id})")
        await respond(response_url, "\n".join(lines))
    else:
        await respond(response_url, "Usage: `/otp latest [N]` | `/otp backtest [hold_days]` | `/otp brief {trade_id|latest}` | `/otp digest [N]`")
