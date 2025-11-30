**Session Recovery / Local Chat History**

- **Purpose**: Store short chat/session dumps locally so reconnects don't lose context.
- **Location**: `.local/tradewatch_session.json` (this directory is ignored by git).
- **Helper script**: `scripts/save_session.py` — append messages and inspect recent entries.

Quick examples:

Save a message as the assistant:

```bash
python3 scripts/save_session.py --role assistant --message "Resumed work: fixed risk endpoint"
```

Append message from stdin:

```bash
echo "note about failing tests" | python3 scripts/save_session.py --role user
```

Show the last 10 entries:

```bash
python3 scripts/save_session.py --show 10
```

If you want, I can wire this into your local workflow or add a tiny VS Code task/snippet.

VS Code integration

- A `tasks.json` is provided at `.vscode/tasks.json` with two convenient tasks:
	- **Save session (prompt)**: prompts you in the integrated terminal to type a short note and saves it.
	- **Save session (from clipboard)**: saves the current clipboard contents as a session note (tries `xclip`, `wl-paste`, `pbpaste`).

Run the tasks via **Terminal → Run Task...** or bind them with a keyboard shortcut in VS Code.

WIP commits (frequent commits)

- There's a helper script at `scripts/wip_commit.sh` to quickly stage and create a local "WIP" commit. Example:

```bash
./scripts/wip_commit.sh --message "WIP: trying containerized frontend"
```

- `scripts/save_session.py` accepts `--wip` to optionally run the WIP helper immediately after saving a session entry:

```bash
python3 scripts/save_session.py --role user --message "investigating Dockerfile issues" --wip
```

- The WIP helper stages tracked changes only by default (`git add -u`) so accidental new files are not committed. Pass `--all` if you want to include untracked files. It is interactive if you omit `--message`.

Notes

- The WIP commits are made in the repository you're working in; they are normal git commits and can be pushed or rolled back normally.
- If you prefer not to commit to the main repo, we can instead create a separate local-only history (e.g. a `.local/history` repo) — tell me if you'd like that alternative.

Working on branches

- By convention commit frequently to the `dev` branch until the feature is stable. The helpers in `scripts/` will prompt you before creating commits on non-`dev` branches.
- I can automatically create a focused commit for the helper files on `dev` so your workspace tracks them — see the commit I create below.

Containerization troubleshooting (quick notes)

- Common issue: the Next.js `web` container cannot reach the API if `NEXT_PUBLIC_API_BASE` is set to `http://localhost:8001`. Inside the `web` container `localhost` points to the container itself. Use the service name `api` (e.g. `http://api:8001`) or configure the host networking appropriately when testing locally.
- Check `deploy/docker-compose.dev.yml`:
	- Set `web.environment.NEXT_PUBLIC_API_BASE` to `http://api:8001` for container-to-container API calls.
	- For browser-based local development (accessing Next from host), you may prefer `http://localhost:8001` but ensure Next's runtime picks the right value (server vs client).
- If you saw build or runtime errors while containerizing the frontend, open `webapp/Dockerfile` and `deploy/docker-compose.dev.yml` — I reviewed them and suggest using the service hostnames for inter-service communication.
