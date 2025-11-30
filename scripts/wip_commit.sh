#!/usr/bin/env bash
set -euo pipefail

# Lightweight helper to create frequent WIP commits.
# Usage:
#   ./scripts/wip_commit.sh --message "WIP: quick note"
#   ./scripts/wip_commit.sh           # will prompt for message

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

MSG=""
ADD_ALL=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --message|-m)
      shift
      MSG="$1"
      shift
      ;;
    --all|-a)
      ADD_ALL=1
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--message|-m MESSAGE] [--all]";
      echo "  --all / -a : Stage tracked + untracked files (default is tracked only)";
      exit 0;
      ;;
    *)
      echo "Unknown arg: $1" >&2; exit 2;
      ;;
  esac
done

if [[ -z "$MSG" ]]; then
  read -r -p "WIP commit message: " MSG
fi

if [[ -z "$MSG" ]]; then
  echo "Empty message, aborting." >&2
  exit 2
fi

# Check current branch and prefer working on 'dev'
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(detached)")
if [[ "$CURRENT_BRANCH" != "dev" ]]; then
  echo "You are on branch '$CURRENT_BRANCH'. It's recommended to commit WIPs on 'dev'."
  read -r -p "Create/switch to 'dev' (will create from current HEAD if missing)? [y/N]: " yn
  if [[ "$yn" =~ ^[Yy]$ ]]; then
    if git rev-parse --verify dev >/dev/null 2>&1; then
      git checkout dev
    else
      git checkout -b dev
    fi
    echo "Now on branch: $(git rev-parse --abbrev-ref HEAD)"
  else
    read -r -p "Proceed committing on '$CURRENT_BRANCH'? [y/N]: " yn2
    if [[ ! "$yn2" =~ ^[Yy]$ ]]; then
      echo "Aborting per user choice." >&2
      exit 1
    fi
  fi
fi

# Show staged/unstaged summary and ask confirmation
echo "Git status summary:"
git status --short --branch
read -r -p "Stage all changes and create WIP commit? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborting — no changes were staged." >&2
  exit 1
fi

if [[ $ADD_ALL -eq 1 ]]; then
  echo "Staging tracked and untracked changes (git add -A)..."
  git add -A
else
  echo "Staging tracked changes only (git add -u). Pass --all to include new files."
  git add -u
fi

echo "Committing as WIP: $MSG"
if git commit -m "WIP: $MSG"; then
  echo "Created WIP commit: $(git rev-parse --short HEAD)"
else
  echo "Nothing to commit or commit failed." >&2
  exit 0
fi
