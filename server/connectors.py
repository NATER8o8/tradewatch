
from __future__ import annotations
from typing import Dict, Any, List, Optional
import io, csv, httpx, os
from .ingest import parse_amount_range

HOUSE_CSV = os.environ.get("HOUSE_DATA_CSV", "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.csv")
SENATE_CSV = os.environ.get("SENATE_DATA_CSV", "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.csv")
UK_CSV = os.environ.get("UK_DATA_CSV", "")  # optional custom source

def _fetch_csv(url: str) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=30.0, headers={"User-Agent":"OfficialTradesPro/1.0"}) as http:
        r = http.get(url)
        r.raise_for_status()
        data = r.text
    rows = list(csv.DictReader(io.StringIO(data)))
    return rows

def fetch_us_house(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = _fetch_csv(HOUSE_CSV)
    out: List[Dict[str, Any]] = []
    for r in rows[:limit or len(rows)]:
        amount_min, amount_max = parse_amount_range(r.get("amount"))
        out.append({"source_url": HOUSE_CSV, 
            "source": "us_house_csv",
            "official_name": r.get("representative") or r.get("name") or "",
            "chamber": "house",
            "state": r.get("state"),
            "ticker": r.get("ticker") or None,
            "issuer": r.get("asset_description") or None,
            "transaction_type": (r.get("type") or "").lower(),
            "owner": (r.get("owner") or "unknown").lower(),
            "amount": r.get("amount"),
            "amount_min": amount_min, "amount_max": amount_max,
            "trade_date": r.get("transaction_date"),
            "reported_date": r.get("disclosure_date") or r.get("filed_date"),
            "filing_url": r.get("ptr_link") or ""
        })
    return out

def fetch_us_senate(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = _fetch_csv(SENATE_CSV)
    out: List[Dict[str, Any]] = []
    for r in rows[:limit or len(rows)]:
        amount_min, amount_max = parse_amount_range(r.get("amount"))
        out.append({"source_url": HOUSE_CSV, 
            "source": "us_senate_csv",
            "official_name": r.get("senator") or r.get("name") or "",
            "chamber": "senate",
            "state": None,
            "ticker": r.get("ticker") or None,
            "issuer": r.get("asset_description") or None,
            "transaction_type": (r.get("type") or "").lower(),
            "owner": "unknown",
            "amount": r.get("amount"),
            "amount_min": amount_min, "amount_max": amount_max,
            "trade_date": r.get("transaction_date") or r.get("date") or r.get("disclosure_date"),
            "reported_date": r.get("disclosure_date") or None,
            "filing_url": r.get("link") or ""
        })
    return out

def fetch_uk_register(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not UK_CSV:
        return []
    rows = _fetch_csv(UK_CSV)
    out: List[Dict[str, Any]] = []
    for r in rows[:limit or len(rows)]:
        out.append({"source_url": HOUSE_CSV, 
            "source": "uk_csv", "source_url": UK_CSV,
            "official_name": r.get("member") or r.get("name") or "",
            "chamber": "other",
            "ticker": r.get("ticker") or None,
            "issuer": r.get("company") or r.get("security") or None,
            "transaction_type": (r.get("type") or "").lower(),
            "owner": "unknown",
            "amount": r.get("amount"),
            "amount_min": None, "amount_max": None,
            "trade_date": r.get("date") or r.get("trade_date"),
            "reported_date": r.get("filed_date") or None,
            "filing_url": r.get("url") or ""
        })
    return out

def dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set(); out = []
    for r in records:
        key = (r.get("source"), (r.get("official_name") or "").strip(), r.get("ticker") or r.get("issuer"), r.get("trade_date"))
        if key in seen: continue
        seen.add(key); out.append(r)
    return out
