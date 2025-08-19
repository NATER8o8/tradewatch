
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

pkg update -y
pkg install -y python nodejs git clang libffi openssl libjpeg-turbo zlib

# Create venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r server/requirements.txt

# Build static web
cd webapp
npm install
npm run build
npx next export
cd ..

# Run API serving static frontend
export SERVE_FRONTEND=1
export USE_REDIS=0         # use LocalQueue
export DATABASE_URL=sqlite:///./otp.db
uvicorn server.app:app --host 0.0.0.0 --port 8001
