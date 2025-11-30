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
PROJECT_CONTEXT = ROOT / "PROJECT_CONTEXT.md"
AUTO_START = "<!-- AUTO_NOTES_START -->"
AUTO_END = "<!-- AUTO_NOTES_END -->"
MAX_NOTES = int(os.environ.get("TW_CONTEXT_MAX_NOTES", "20"))


def current_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def append_entry(role: str, message: str) -> dict:
    ensure_dir()
    entry = {
        "timestamp": current_timestamp(),
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
                return entry
        except Exception:
            pass

    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump([entry], f, indent=2, ensure_ascii=False)
    return entry


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


def normalize_message(msg: str) -> str:
    # Collapse whitespace/newlines for context file entries
    return " ".join(msg.strip().split())


def ensure_context_markers(text: str) -> str:
    if AUTO_START in text and AUTO_END in text:
        return text
    extra = "\n\n## Latest Notes\n_Auto-updated by `scripts/save_session.py`. Newest first. Keep the markers below in place._\n\n"
    extra += AUTO_START + "\n" + AUTO_END + "\n"
    return text.rstrip() + extra


def update_project_context(entry: dict):
    if not PROJECT_CONTEXT.exists():
        # Nothing to update; context file optional
        return
    text = PROJECT_CONTEXT.read_text(encoding="utf-8")
    text = ensure_context_markers(text)
    start_idx = text.find(AUTO_START)
    end_idx = text.find(AUTO_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return
    start_idx += len(AUTO_START)
    before = text[:start_idx]
    block = text[start_idx:end_idx]
    after = text[end_idx:]
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    new_line = f"- [{entry.get('timestamp','?')}] {entry.get('role','?')}: {normalize_message(entry.get('message',''))}"
    notes = [new_line]
    for ln in lines:
        if ln != new_line:
            notes.append(ln)
    notes = notes[:MAX_NOTES]
    notes_text = ("\n".join(notes) + "\n") if notes else "\n"
    new_content = before + "\n" + notes_text + after
    PROJECT_CONTEXT.write_text(new_content, encoding="utf-8")


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

    entry = append_entry(args.role, msg)
    update_project_context(entry)
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
