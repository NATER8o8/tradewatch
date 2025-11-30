#!/usr/bin/env python3
"""Small helper to save and show local session/chat history.

The file is written to `.local/tradewatch_session.json` (ignored by git).
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SESSION_DIR = ROOT / ".local"
SESSION_FILE = SESSION_DIR / "tradewatch_session.json"


def ensure_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def append_entry(role: str, message: str) -> None:
    ensure_dir()
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "role": role,
        "message": message,
    }

    if SESSION_FILE.exists():
        try:
            with SESSION_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                data.append(entry)
                with SESSION_FILE.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return
        except Exception:
            pass

    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump([entry], f, indent=2, ensure_ascii=False)


def show_last(n: int):
    if not SESSION_FILE.exists():
        return []
    try:
        with SESSION_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data[-n:]
    except Exception:
        return []
    return []


def main():
    parser = argparse.ArgumentParser(description="Save or show local session entries")
    parser.add_argument("--role", choices=["user", "assistant", "system"], default="user")
    parser.add_argument("--message", help="Message to append. If omitted, reads stdin.")
    parser.add_argument("--show", type=int, help="Show last N entries and exit")
    parser.add_argument("--wip", action="store_true", help="Create a WIP git commit after saving the session (stages all changes)")
    args = parser.parse_args()

    if args.show:
        for e in show_last(args.show):
            ts = e.get("timestamp", "?")
            role = e.get("role", "?")
            msg = e.get("message", "")
            print(f"[{ts}] {role}: {msg}")
        return

    msg = args.message
    if not msg:
        msg = sys.stdin.read().strip()
    if not msg:
        print("No message provided", file=sys.stderr)
        sys.exit(2)

    append_entry(args.role, msg)
    print("Saved to", SESSION_FILE)

    if args.wip:
        # Try to run the wip commit helper non-interactively
        script = Path(__file__).resolve().parents[0] / "wip_commit.sh"
        if not script.exists():
            script = Path(__file__).resolve().parents[1] / "scripts" / "wip_commit.sh"
        if script.exists():
            try:
                subprocess.run([str(script), "--message", f"Session: {msg[:200]}"], check=True)
            except subprocess.CalledProcessError as e:
                print("WIP commit failed:", e, file=sys.stderr)
        else:
            print("WIP helper script not found at scripts/wip_commit.sh", file=sys.stderr)


if __name__ == "__main__":
    main()
