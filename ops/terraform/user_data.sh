
#cloud-config
package_update: true
runcmd:
  - [ bash, -lc, "apt-get update && apt-get install -y docker-compose git" ]
  - [ bash, -lc, "git clone https://github.com/you/official-trades-pro /opt/otp || true" ]
  - [ bash, -lc, "cd /opt/otp && cp .env.example .env && sed -i 's/example.com/${domain}/g' .env" ]
  - [ bash, -lc, "cd /opt/otp && docker compose -f docker-compose.prod.yml up -d --build" ]
