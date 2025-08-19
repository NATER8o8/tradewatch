
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from .db import SessionLocal
from .connectors import fetch_us_senate, fetch_us_house, fetch_uk_register, dedupe
from .ingest import persist_records

def start_scheduler(app: FastAPI):
    scheduler = AsyncIOScheduler()

    async def run_all():
        if os.environ.get("INGEST_ENABLED", "1") != "1":
            return
        with SessionLocal() as db:
            recs = []
            try: recs += fetch_us_house(limit=None)
            except Exception as e: print("house fetch error", e)
            try: recs += fetch_us_senate(limit=None)
            except Exception as e: print("senate fetch error", e)
            try: recs += fetch_uk_register(limit=None)
            except Exception as e: print("uk fetch error", e)
            unique = dedupe(recs)
            try:
                added = persist_records(db, unique)
                print(f"Ingest: added {added} records")
            except Exception as e:
                print("persist error", e)

    scheduler.add_job(run_all, "cron", hour=3, minute=15)
    scheduler.start()
