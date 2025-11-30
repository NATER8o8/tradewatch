#!/usr/bin/env python3
"""
Simple polling file-watcher that detects modifications to tracked files
and calls `scripts/save_session.py` with a short message listing changed files.

This avoids external deps and is good enough for local dev usage. Run it
as a long-running task in VS Code: it will auto-create session entries
when you save files in the repo.
"""
import os
import sys
import time
import subprocess
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH_INTERVAL = float(os.environ.get("TW_WATCH_INTERVAL", "1.0"))


def get_tracked_files() -> List[str]:
    # Use git ls-files to restrict to tracked files (fast and simple)
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=ROOT)
        files = [os.path.join(ROOT, p.strip()) for p in out.decode().splitlines() if p.strip()]
        return files
    except Exception:
        # Fallback: watch everything under repo (may be noisy)
        tracked = []
        for dirpath, dirnames, filenames in os.walk(ROOT):
            # skip .git and .local by default
            if ".git" in dirpath.split(os.sep) or dirpath.startswith(os.path.join(ROOT, '.local')):
                continue
            for f in filenames:
                tracked.append(os.path.join(dirpath, f))
        return tracked


def stat_mtimes(files: List[str]) -> Dict[str, float]:
    mt: Dict[str, float] = {}
    for f in files:
        try:
            mt[f] = os.path.getmtime(f)
        except Exception:
            continue
    return mt


def run_save_session(changed: List[str]):
    if not changed:
        return
    msg = "Auto-save: " + ", ".join(os.path.relpath(p, ROOT) for p in changed[:10])
    cmd = ["python3", os.path.join(ROOT, "scripts", "save_session.py"), "--role", "assistant", "--message", msg]
    try:
        subprocess.run(cmd, cwd=ROOT, check=False)
    except Exception:
        pass


def main():
    print("Starting file-watcher (polling). Press CTRL+C to stop.")
    files = get_tracked_files()
    mt = stat_mtimes(files)
    try:
        while True:
            time.sleep(WATCH_INTERVAL)
            files = get_tracked_files()
            new_mt = stat_mtimes(files)
            changed = []
            for f, m in new_mt.items():
                old = mt.get(f)
                if old is None:
                    changed.append(f)
                elif m > old + 1e-6:
                    changed.append(f)
            if changed:
                run_save_session(changed)
            mt = new_mt
    except KeyboardInterrupt:
        print('\nFile-watcher stopped by user')


if __name__ == '__main__':
    main()
