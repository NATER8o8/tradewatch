#!/usr/bin/env bash
set -euo pipefail
# Copies hook templates from `hooks/` into `.git/hooks` so they run locally.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC_DIR="$REPO_ROOT/hooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$GIT_HOOKS_DIR" ]; then
  echo "This does not look like a git repo (no .git/hooks)." >&2
  exit 1
fi

for f in "$HOOK_SRC_DIR"/*; do
  name=$(basename "$f")
  dest="$GIT_HOOKS_DIR/$name"
  echo "Installing hook $name -> $dest"
  cp "$f" "$dest"
  chmod +x "$dest"
done

echo "Hooks installed. Post-commit will call scripts/save_session.py after commits."
