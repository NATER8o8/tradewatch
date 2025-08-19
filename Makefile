
.PHONY: setup api worker web migrate revision seed export smoke
PY := python
PIP := pip
setup:
	$(PY) -m venv .venv && . .venv/bin/activate && $(PIP) install -r server/requirements.txt
api:
	. .venv/bin/activate && uvicorn server.app:app --reload --port 8001
worker:
	. .venv/bin/activate && $(PY) -m server.worker
migrate:
	. .venv/bin/activate && alembic upgrade head
revision:
	. .venv/bin/activate && alembic revision --autogenerate -m "$(m)"
seed:
	. .venv/bin/activate && $(PY) -m server.seed
web:
	cd webapp && npm install && npm run dev
export:
	curl -sS 'http://localhost:8001/api/export/trades.csv' -o trades.csv && echo "Saved trades.csv"
smoke:
	. .venv/bin/activate && $(PY) scripts/smoke.py
