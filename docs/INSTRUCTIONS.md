
Deployment refinements added:
- HTTPS local mode with self-signed cert (scripts/run_https.sh).
- First-run setup page (/setup) to generate/store API token in DB; admin auth reads from env or DB.
- Provenance snapshots for ingested trades (trade_sources table) including raw CSV row and source URL.
- Android-friendly export: POST /api/export/save?fmt=csv|jsonl writes to /sdcard/Download.
- Service worker notification test button on Dashboard.
- All documentation, including these instructions, is included in docs/INSTRUCTIONS.md.


## New features in this drop
- Web Push (VAPID): `/api/push/public_key`, `/api/push/register`, `/api/push/test`, and `scripts/generate_vapid.py` to create keys in DB.
- Provenance UI at `/provenance` and API `/api/trades/{id}/sources`.
- Data Quality report at `/quality` and API `/api/admin/quality/report`.
- First‑run Checklist at `/checklist` to automate setup steps.
- TWA guide at `docs/twa_guide.md` for Play Store packaging.


## Deployment (new)
### Docker Compose
- See `deploy/docker-compose.yaml` and `deploy/nginx.conf`.
- Services: Postgres, Redis, API, worker, Next.js web, nginx with certbot.

### Terraform (DigitalOcean)
- See `deploy/main.tf`.
- Requires `do_token` and `ssh_fingerprint` variables.
- Creates a droplet with Docker ready. Then run `docker compose up -d`.

### Costs
- **Droplet (s-2vcpu-4gb)** ≈ $24/mo.
- Block storage (DB snapshots) optional, ~$10/mo for 100GiB.
- Bandwidth: 1TB included, $0.01/GB over.
- Certbot renewal: free with Let's Encrypt.


## Production bundle included
- `docker-compose.prod.yml` with Nginx + Certbot + API + Web + DB + Redis + Worker
- `ops/nginx.conf` preconfigured for `/api/*` proxy and static site
- Terraform scripts in `ops/terraform/` for DigitalOcean one-click infra
- S3 provenance snapshots (set `S3_BUCKET`, `AWS_*` envs) with presigned URLs
- Webhooks with retries & DLQ (`/api/admin/webhooks/dlq`, `/api/admin/webhooks/requeue`)
- Email digests templating (`server/digests.py`)

## RBAC & rate limits
- Plans stored as `settings` with key `plan:<email>` → values: `free|pro|enterprise`
- API rate/min scales by plan; export and alerts limited per plan.

## Deploy quickstart
- Local prod: `docker compose -f docker-compose.prod.yml up -d --build`
- DO: `scripts/deploy_do.sh` (requires `doctl`, Terraform, env: `DOMAIN`, `API_TOKEN`, `DO_ACCESS_TOKEN`)


## Observability add-on
- Launch Prometheus + Grafana:
```
docker compose -f docker-compose.observability.yml up -d
```
Grafana at http://localhost:3001 (anonymous view).

## S3 lifecycle
```
AWS_* env + S3_BUCKET set
python scripts/s3_lifecycle.py --prefix provenance/ --days 90
```

## Insider‑risk
- API: `GET /api/risk/officials`
- UI: `/risk`

## TWA scaffolding
```
npm i -g @bubblewrap/cli
export DOMAIN=your-domain.com
bash scripts/twa_init.sh
```
Open the generated project in Android Studio and build a signed APK/AAB.
