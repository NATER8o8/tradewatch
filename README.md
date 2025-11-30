
# Official Trades Pro — MAX++++++++++ (2025-08-19)

**What’s inside**
- FastAPI API (trades, briefs, backtests), Slack commands, Jobs queue (RQ/Redis)
- OCR-ready parser stubs, CSV/JSON/JSONL exports, GZip
- Alembic migrations + seed, Prometheus metrics, health checks
- Next.js UI (Dashboard, Jobs)

## Quickstart
```bash
make setup
make migrate && make seed
make api        # API on :8001
make worker     # RQ worker
# In another terminal:
cd webapp && npm install && npm run dev  # :3000
```

## Build
```bash
# Install backend deps, create venv, and compile + export the Next.js app
make build
```

The `build` target chains the Python setup (virtualenv + `server/requirements.txt`)
and the production Next.js export so a fresh clone ends up with both layers ready.
The export lands in `webapp/out`, which FastAPI can serve directly when
`SERVE_FRONTEND=1`.

## Containerized dev stack
```bash
# bring up Postgres, Redis, API, worker, and Next dev server
docker compose -f deploy/docker-compose.dev.yml up --build
```

- The `web` service runs `npm run dev` in a container, mounts `webapp/` from the host,
  and exposes port `3000` (edit locally, refresh the browser).
- API + worker containers hot-reload the mounted `server/` directory and expose port `8001`.
- Override `NEXT_PUBLIC_API_BASE` if your browser should talk to a different API host.
- To seed demo trades inside the stack, run  
  `docker compose -f deploy/docker-compose.dev.yml run --rm api python -m server.seed`.
- Stop everything with `docker compose -f deploy/docker-compose.dev.yml down`.

## Slack commands
- `/otp brief {trade_id}`, `/otp brief`, `/otp brief latest`
- `/otp digest [N]`
- `/otp backtest [days]`
- `/otp latest [N]`

## Exports
- CSV: `/api/export/trades.csv`, `/api/export/backtest.csv?hold_days=30`
- JSONL: `/api/export/trades.jsonl`
- JSON: `/api/export/backtest.json?hold_days=30`
(Responses are gzipped when large via middleware.)

## Monitoring
- `/healthz` (Redis + DB ping)
- `/metrics` Prometheus: `otp_http_requests_total`, `otp_http_request_seconds_*`

## ENV
Set as needed:
```
REDIS_URL=redis://localhost:6379/0
PUBLIC_BASE_URL=http://localhost:8001
FRONTEND_BASE_URL=http://localhost:3000
DATABASE_URL=sqlite:///./otp.db
```

## Real connectors
Defaults use community mirrors of official disclosures:
- House: env `HOUSE_DATA_CSV` (default S3 all_transactions.csv)
- Senate: env `SENATE_DATA_CSV` (default S3 all_transactions.csv)
- UK (optional): env `UK_DATA_CSV` (CSV with columns: name/member, company/security, ticker?, type, amount, date, url)

Admin:
- `POST /api/admin/ingest/run?source=us-house|us-senate|uk&persist=1`
- `POST /api/admin/ingest/run_all?limit=50&persist=1`

Scheduler:
- Nightly ingestion at 03:15 UTC (set `INGEST_ENABLED=0` to disable).


## Android Tablet Deployment (Termux)
> Works offline with SQLite + LocalQueue (no Redis/Postgres required). Frontend served by FastAPI.

```bash
# On Android, install Termux from F-Droid, then:
git clone <your-repo>
cd official-trades-pro
bash scripts/android_bootstrap.sh
# App runs at http://127.0.0.1:8001 (PWA installable from Chrome)
```

To restart after first setup:
```bash
bash scripts/run_android.sh
```

### PWA
- Manifest & service worker included. Install to home screen for a full-screen experience.
- Static Next.js export served by FastAPI when `SERVE_FRONTEND=1`.

### Search
- SQLite FTS5 auto-initialized on startup (SQLite-only). Endpoint: `GET /api/search?q=...`.


## HTTPS (self-signed, local)
```bash
bash scripts/run_https.sh   # serves on https://localhost:8443
```
Chrome will warn about the self-signed cert; proceed to enable PWA features.

## First-run wizard
Open `/setup` to initialize an admin API token (stored in the DB settings table).

## Provenance
Every persisted trade stores a `trade_sources` row with the raw CSV JSON and the source URL (if available).

## Android export to Downloads
On Termux, run `termux-setup-storage` once, then:
```bash
curl -X POST http://127.0.0.1:8001/api/export/save?fmt=csv
# -> /sdcard/Download/official-trades.csv
```
