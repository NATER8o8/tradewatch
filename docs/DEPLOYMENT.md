
# Production Deployment

## Docker Compose (Nginx + Certbot + API + Web + DB + Redis + Worker)

1) Set env:
```
cp .env.example .env
# edit .env with DOMAIN, API_TOKEN, AWS creds (optional for S3)
```
2) Build & run:
```
docker compose -f docker-compose.prod.yml up -d --build
```
3) Obtain certs:
- Create DNS A record for your `DOMAIN` pointing to the host.
- Run certbot in webroot mode (handled by compose). First issuance example:
```
docker run --rm -it -v certbot_www:/var/www/certbot -v certbot_etc:/etc/letsencrypt certbot/certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --agree-tos -m you@example.com --no-eff-email
docker compose -f docker-compose.prod.yml restart nginx
```

## DigitalOcean (Terraform)
See `ops/terraform/README.md` for setup. The cloud-init script pulls the repo and runs the production compose stack.


## Observability
Start Prometheus and Grafana alongside your prod stack:
```
docker compose -f docker-compose.prod.yml -f docker-compose.observability.yml up -d
```
Then open Grafana at :3001 (default anonymous viewer) and explore the pre-provisioned **OTP** dashboard.
