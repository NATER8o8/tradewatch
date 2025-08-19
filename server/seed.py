
from datetime import date, timedelta
from .db import SessionLocal
from .models import Official, Trade, Chamber, TxType, Owner
def run():
    with SessionLocal() as db:
        if db.query(Official).count() > 0:
            print("Seed skipped (data exists)."); return
        off1 = Official(name="Alex Example", chamber=Chamber.senate, role="Senator", state="CA", committees="Finance;Technology")
        off2 = Official(name="Jamie Demo", chamber=Chamber.house, role="Representative", state="NY", committees="Energy;Commerce")
        db.add_all([off1, off2]); db.commit(); db.refresh(off1); db.refresh(off2)
        t1 = Trade(official_id=off1.id, transaction_type=TxType.buy, owner=Owner.self, trade_date=date.today()-timedelta(days=3), reported_date=date.today(), ticker="AAPL", amount_min=10000, amount_max=15000, filing_url="https://example.com/filing1.pdf")
        t2 = Trade(official_id=off2.id, transaction_type=TxType.sell, owner=Owner.spouse, trade_date=date.today()-timedelta(days=10), reported_date=date.today()-timedelta(days=2), ticker="MSFT", amount_min=5000, amount_max=10000, filing_url="https://example.com/filing2.pdf")
        db.add_all([t1, t2]); db.commit(); print("Seed complete.")
if __name__ == "__main__":
    run()
