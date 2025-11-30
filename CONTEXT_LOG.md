# Conversation Context Snapshot

_Generated: 2025-11-30T22:11:54.580872Z_

## Project Context Snapshot

# Project Context

_Updated: 2025-11-30_

This file captures the running context so a new chat/session can resume quickly.

## Current Focus
- Containerize the Next.js frontend and run it via the Docker dev stack alongside API/worker.
- Keep helper scripts (session logging, WIP commits, hooks) usable across sessions.

## Recent Changes
1. **Safer WIP commits** – `scripts/wip_commit.sh` now stages tracked files by default, `--all` opt-in, docs updated (`SESSION_RECOVERY.md`).
2. **Frontend build/export workflow** – `webapp/package.json`, `Makefile`, `scripts/android_bootstrap.sh`, `docker-compose.prod.yml`, `README.md` updated so `npm run build-export` produces `webapp/out`, `make build` includes the export, and prod compose shares the build with nginx.
3. **Helper tooling** – Added `.gitignore` entries for runtime logs/PIDs, `scripts/file_watcher.py`, `scripts/install_hooks.sh`, and `hooks/post-commit` to auto-log activity.

## Outstanding Tasks
- **Docker permissions**: Host user lacks permission to talk to Docker daemon (`dial unix /var/run/docker.sock: connect: permission denied`). Fix by ensuring `mcp` is in the `docker` group and reloading the session (`newgrp docker` or log out/in) before re-running `docker compose -f deploy/docker-compose.dev.yml up --build`.
- **Test containerized frontend**: Once Docker works, start the dev stack, browse `http://localhost:3000`, and confirm it reaches the API (`http://localhost:8001`).
- **Signed commits**: Current commits were made without signatures (signing disabled temporarily). Recreate them with signing enabled if required.

## Latest Notes
_Auto-updated by `scripts/save_session.py`. Newest first. Keep the markers below in place._

<!-- AUTO_NOTES_START -->
- [2025-11-30T22:11:54.580586Z] user: Context sync check
- [2025-11-30T22:11:04.270909Z] user: Sync context log
- [2025-11-30T22:09:44.421235Z] user: Context update placeholder
- [2025-11-30T03:08:36.645435Z] user: saving session
<!-- AUTO_NOTES_END -->

## Useful Commands
```bash
docker compose -f deploy/docker-compose.dev.yml up --build     # dev stack
docker compose -f deploy/docker-compose.dev.yml logs -f web    # watch frontend
docker compose -f deploy/docker-compose.dev.yml down           # stop stack
python3 scripts/save_session.py --message "note"               # append local session log
./scripts/wip_commit.sh --message "..." [--all]                # WIP commits (tracked-only default)
```

## Tips
- If chat resets, skim this file plus `SESSION_RECOVERY.md` to restore context.
- Update this file after significant milestones (new tasks, blockers, completed work) so the next session has an accurate snapshot.

## Latest Session Notes (newest first)

- [2025-11-30T22:11:54.580586Z] user: Context sync check
- [2025-11-30T22:11:04.270909Z] user: Sync context log
- [2025-11-30T22:09:44.421235Z] user: Context update placeholder
- [2025-11-30T03:08:36.645435Z] user: saving session
- [2025-11-30T01:58:31.001456Z] assistant: session recovery test from copilot

## Session Entry Count

5
