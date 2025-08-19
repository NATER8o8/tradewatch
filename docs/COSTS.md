
# Hosting Cost Notes (estimates)

## DigitalOcean
- Droplet (s-2vcpu-4gb): ~$28/mo
- Block storage (optional): $0.10/GB-mo
- Managed DBs (optional alternative): $15–$30+/mo
- Bandwidth: included generous egress for droplet

## Other services
- S3-compatible storage (DO Spaces or AWS S3): ~$5/mo + storage/egress
- Email (e.g., Postmark/SES): ~$10/mo tier or pay-as-you-go
- Domain: ~$10–$15/yr

## Scaling guidance
- Move from SQLite → Postgres (already in prod compose).
- Horizontal: multiple API containers behind Nginx; add a worker replica.
- Caching & queues: Redis (already in stack).
- Monitoring: Prometheus + Grafana (add-ons; metrics endpoint already exposed).


## Add-on costs
- Prometheus/Grafana on the same droplet: minimal extra cost; consider a larger droplet (e.g., s-4vcpu-8gb) for busy sites.
- S3 lifecycle reduces storage costs automatically (older provenance pruned after N days).
- Play Store: one-time $25 developer account.
