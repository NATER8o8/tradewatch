#!/usr/bin/env bash
set -euo pipefail

# Create a local-only history repo under .local/history by snapshotting the working tree.
# Usage: ./scripts/local_history.sh --message "note"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HISTORY_DIR="$REPO_ROOT/.local/history"

MSG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --message|-m)
      shift; MSG="$1"; shift;;
    --help|-h)
      echo "Usage: $0 [--message|-m MESSAGE]"; exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "$MSG" ]]; then
  read -r -p "Snapshot message: " MSG
fi

mkdir -p "$REPO_ROOT/.local"

if [[ ! -d "$HISTORY_DIR/.git" ]]; then
  echo "Initializing local history repo at $HISTORY_DIR"
  rm -rf "$HISTORY_DIR"
  mkdir -p "$HISTORY_DIR"
  git -C "$HISTORY_DIR" init
  git -C "$HISTORY_DIR" config user.name "local-history"
  git -C "$HISTORY_DIR" config user.email "local@local"
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Copying project files to snapshot area (excluding .git and .local)..."
rsync -a --exclude ".git" --exclude ".local" --delete "$REPO_ROOT/" "$TMPDIR/project/"

# Replace history working tree with snapshot
rm -rf "$HISTORY_DIR/worktree"
mkdir -p "$HISTORY_DIR/worktree"
rsync -a --delete "$TMPDIR/project/" "$HISTORY_DIR/worktree/"

cd "$HISTORY_DIR"
git add -A
git commit -m "SNAPSHOT: $MSG" || echo "No changes to snapshot"
echo "Snapshot recorded in $HISTORY_DIR: $(git rev-parse --short HEAD 2>/dev/null || echo '(none)')"
