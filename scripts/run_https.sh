
#!/usr/bin/env bash
set -euo pipefail
[ -f certs/cert.pem ] || bash scripts/generate_cert.sh
export SERVE_FRONTEND=1
export USE_REDIS=0
export DATABASE_URL=sqlite:///./otp.db
uvicorn server.app:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
