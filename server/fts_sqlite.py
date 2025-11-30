
from sqlalchemy import text
from .db import engine, DATABASE_URL

def init_sqlite_fts():
    if not str(DATABASE_URL).startswith('sqlite'):
        return
    with engine.connect() as conn:
        # Create an independent FTS5 table (no `content=` mapping) so columns
        # like `official_name` and `chamber` (which live on `officials`) don't
        # get resolved against the `trades` table and cause missing-column errors.
        conn.execute(text("""CREATE VIRTUAL TABLE IF NOT EXISTS trades_fts USING fts5(
  ticker, issuer, transaction_type, owner, official_name, chamber, filing_url, created_at, trade_date, reported_date
);
"""))
        # Try to populate and wire triggers; failures (schema mismatch, missing
        # columns) should not prevent the app from starting — tests only need
        # this to be non-fatal.
        try:
            conn.execute(text("""INSERT INTO trades_fts(rowid, ticker, issuer, transaction_type, owner, official_name, chamber, filing_url, created_at, trade_date, reported_date)
SELECT t.id, t.ticker, t.issuer, t.transaction_type, t.owner, o.name, o.chamber, t.filing_url, t.created_at, t.trade_date, t.reported_date
FROM trades t LEFT JOIN officials o ON t.official_id = o.id
WHERE NOT EXISTS (SELECT 1 FROM trades_fts WHERE rowid = t.id);
"""))
            # triggers
            conn.execute(text("""CREATE TRIGGER IF NOT EXISTS trg_trades_ai AFTER INSERT ON trades BEGIN
  INSERT INTO trades_fts(rowid, ticker, issuer, transaction_type, owner, official_name, chamber, filing_url, created_at, trade_date, reported_date)
  SELECT new.id, new.ticker, new.issuer, new.transaction_type, new.owner, (SELECT name FROM officials WHERE id=new.official_id), (SELECT chamber FROM officials WHERE id=new.official_id), new.filing_url, new.created_at, new.trade_date, new.reported_date;
END;
"""))
            conn.execute(text("""CREATE TRIGGER IF NOT EXISTS trg_trades_ad AFTER DELETE ON trades BEGIN
  INSERT INTO trades_fts(trades_fts, rowid) VALUES('delete', old.id);
END;
"""))
            conn.commit()
        except Exception:
            # Best-effort only; ignore population/trigger failures.
            pass
