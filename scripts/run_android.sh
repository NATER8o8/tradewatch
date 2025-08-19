
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
source .venv/bin/activate || true
export SERVE_FRONTEND=1
export USE_REDIS=0
export DATABASE_URL=sqlite:///./otp.db
uvicorn server.app:app --host 0.0.0.0 --port 8001
