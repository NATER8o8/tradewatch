
#!/usr/bin/env bash
set -euo pipefail
if ! command -v doctl >/dev/null 2>&1; then
  echo "Install doctl (DigitalOcean CLI) first."
  exit 1
fi
: "${DOMAIN:?Set DOMAIN env}"
: "${API_TOKEN:?Set API_TOKEN env}"
: "${DO_ACCESS_TOKEN:?Set DO_ACCESS_TOKEN env}"
export TF_VAR_do_token="$DO_ACCESS_TOKEN"
( cd ops/terraform && terraform init && terraform apply -auto-approve -var="domain=$DOMAIN" )
echo "Provisioned. Point your DNS A record to the droplet IP shown above."
