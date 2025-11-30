Containerized development
=========================

This file documents how to run the repo in a local, containerized development
environment using Docker Compose.

Prerequisites
-------------
- Docker Engine (or Podman with Docker-compat)
- Docker Compose plugin (usually `docker compose`)

Files added
-----------
- `deploy/docker-compose.dev.yml` — Docker Compose stack for dev: Postgres, Redis, API, worker, and Next dev server.
- `server/Dockerfile` — minimal image for FastAPI dev server (runs `uvicorn` with `--reload`).
- `webapp/Dockerfile` — minimal image for Next.js dev server.

Run the dev stack
-----------------
From repo root:

```bash
# build and start the dev stack (detached)
docker compose -f deploy/docker-compose.dev.yml up --build -d

# follow logs for API
docker compose -f deploy/docker-compose.dev.yml logs -f api

# check health
curl http://localhost:8001/healthz

# frontend dev at http://localhost:3000
```

Notes & troubleshooting
-----------------------
- The dev compose file mounts local source into the containers so code changes appear
  immediately (hot reload for both uvicorn and Next). If you prefer immutable images,
  remove the `volumes` entries in `deploy/docker-compose.dev.yml`.
- If builds fail because system packages are missing for optional native deps, install
  the packages locally (or extend the Dockerfiles to install extras you need).
- If you don't have Docker on this machine, install it (Ubuntu example):

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmour -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
```

After adding yourself to the `docker` group you may need to re-login.
