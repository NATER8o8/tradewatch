#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PY:-python3}"
PIP_BIN="${PIP:-pip3}"
NODE_BIN="${NODE:-node}"
NPM_BIN="${NPM:-npm}"

step() { echo "[setup] $1"; }

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python binary '$PYTHON_BIN' not found. Set PY=python3 (or similar) before running." >&2
  exit 1
fi
if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  echo "Node.js binary '$NODE_BIN' not found. Install Node 18+ and rerun." >&2
  exit 1
fi
if ! command -v "$NPM_BIN" >/dev/null 2>&1; then
  echo "npm binary '$NPM_BIN' not found. Install npm and rerun." >&2
  exit 1
fi

step "Creating virtualenv (.venv)"
cd "$REPO_ROOT"
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip setuptools wheel

step "Installing backend dependencies"
pip install -r server/requirements.txt

step "Installing frontend dependencies"
cd "$REPO_ROOT/webapp"
"$NPM_BIN" install

step "Setup complete"
