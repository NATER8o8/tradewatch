Purpose
-------
This file tells AI coding assistants how to be immediately productive in this repository. It focuses on the actual structure, runtime commands, integration points, and concrete examples found in the codebase (no generic advice).

Big picture
-----------
- Backend: `server/` — FastAPI app (`server.app`) with SQLAlchemy models (`server/models.py`), Alembic migrations in `server/alembic`, and background jobs via RQ/Redis (`server/tasks.py`, `server/worker.py`).
- Frontend: `webapp/` — Next.js app. Dev server is `next dev`; production build is `next build`.
- Infra & ops: `deploy/`, `ops/`, and `scripts/` contain compose files, terraform, and helper scripts (e.g. `scripts/run_https.sh`, `scripts/android_bootstrap.sh`).

Quick developer workflows (explicit commands)
-------------------------------------------
- Create env + install: `make setup` (creates venv, installs `server/requirements.txt`).
- Run API locally: `make api` (starts `uvicorn server.app:app --reload --port 8001`).
- Run background worker: `make worker` (runs `python -m server.worker`).
- Run migrations: `make migrate` (runs `alembic upgrade head`).
- Make a migration: `make revision m="message"` (autogenerate change against `server/models.py`).
- Seed DB: `make seed` (runs `python -m server.seed`).
- Frontend dev: `cd webapp && npm install && npm run dev` (port 3000). Or use `make web`.
- Full build: `make build` (backend venv + `web-build`).

Important environment variables
-------------------------------
- `DATABASE_URL` — used by `server/db.py` and Alembic (default: `sqlite:///./otp.db`).
- `REDIS_URL` — default Redis for RQ jobs. Background worker uses `server/redis_client.py`.
- `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL` — used by CORS and generated URLs.
- `SERVE_FRONTEND=1` — FastAPI will mount `webapp/out` as static root (see `server/app.py` startup).
- `INGEST_ENABLED`, `HOUSE_DATA_CSV`, `SENATE_DATA_CSV`, `UK_DATA_CSV` — ingestion/connectors settings.

Project-specific conventions and patterns
----------------------------------------
- DB sessions: use `SessionLocal()` from `server/db.py` and `Depends(db_session)` in endpoints (see `server/app.py`).
- Alembic config: `server/alembic/env.py` sets `sqlalchemy.url` to `DATABASE_URL`. For SQLite `render_as_batch` is enabled.
- Background jobs: jobs are queued via `rq` and consumed by `server.worker` (RQ Worker). Use `tasks.enqueue_backtest(...)` as an example.
- Auth & admin gates: token-protected admin endpoints use `require_api_token`; subscription gating uses `require_active_subscription` (see `server/auth.py` and `server/billing.py`).
- AI/briefing: brief generation is implemented in `server/ai.py::make_brief` and called from `POST /api/brief/{trade_id}` in `server/app.py` — that's the place to change AI prompt/behavior.
- Exports & large responses: responses are gzipped via middleware; large CSV/JSONL export endpoints exist under `/api/export/*`.

Integration points & external dependencies
-----------------------------------------
- Redis + RQ: background queue (see `server/redis_client.py`, `server/tasks.py`).
- Database: SQLAlchemy + Alembic; default SQLite for quick dev, but `DATABASE_URL` can point to Postgres.
- S3/Boto3: connectors may read from S3 (see `server/connectors.py` and `server/storage_s3.py`).
- Email/Push: `pywebpush`, `boto3` and `web-push` related code in `server/push.py` and `server/email_service.py`.
- Files & OCR: `PyMuPDF`, `pytesseract` used in `server/pdf_viewer.py`.
- Market data: `yfinance` used by backtest helpers.

Where to look for common edits (concrete file pointers)
----------------------------------------------------
- Add/modify endpoints: `server/app.py` (FastAPI routes).
- Change models/schema: `server/models.py` and then run `make revision` + `make migrate`.
- Background task logic: `server/tasks.py` and worker loop in `server/worker.py`.
- Brief/AI behavior: `server/ai.py` (currently a small function; replace with a call to external LLM or prompt templates here).
- Ingestion connectors: `server/connectors.py` + `server/ingest.py`.
- Migrations: `server/alembic/` and `server/alembic/env.py`.

Small examples
--------------
- Generate a brief (curl):
  - `curl -X POST http://localhost:8001/api/brief/123` (requires subscription/auth flows if enabled).
- Enqueue a backtest job (background):
  - `curl -X POST 'http://localhost:8001/api/backtest/jobs?hold_days=30'`
- Run worker locally:
  - `make worker` (ensure `REDIS_URL` points to running Redis).

Tests & quick checks
--------------------
- Tests: `pytest` is available via `server/requirements.txt`. Run inside venv: `. .venv/bin/activate && pytest -q` or `pytest server/test_smoke.py` for a quick check.
- Health & metrics endpoints: `GET /healthz`, `GET /metrics` (Prometheus client exports metrics names like `otp_http_requests_total`).

Notes for AI agent behavior (how to make safe/accurate edits)
-----------------------------------------------------------
- Prefer small, single-purpose changes and run unit/smoke checks (`pytest` or `make smoke`).
- When changing DB models, always create an Alembic revision (`make revision m="..."`) and migrate (`make migrate`).
- When adding endpoint behavior that enqueues work, update `server/tasks.py` and ensure `make worker` can run against Redis.
- For UI changes, update `webapp/` and run `cd webapp && npm run dev` to verify in the browser.

If something's not discoverable here
----------------------------------
- Ask for missing env values or secrets (we cannot guess deploy-only credentials).
- If unsure whether to use Redis vs LocalQueue for Android, check `scripts/android_bootstrap.sh` and `server/local_queue.py`.

End of instructions — please tell me any missing details or preferences to iterate.
