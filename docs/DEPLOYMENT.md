# Deployment Guide

## Docker Compose Deployment

Docker Compose is the recommended option for local use and private-network deployments.

```bash
docker compose up --build -d
docker compose ps
```

The application is available at `http://localhost:8080`. The API is not exposed directly; Nginx forwards `/api` requests over the private Compose network.

To view logs or stop the application:

```bash
docker compose logs -f
docker compose down
```

No volume is configured because sessions should not survive a restart.

## Development Without Docker

Requirements:

- Python 3.11 or newer
- Node.js 22 or newer
- npm

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
pip install ./lab/instagrapi
PYTHONPATH=src uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd src/frontend
npm ci
npm run dev
```

Vite serves the interface on `http://localhost:5173` and proxies `/api` to port 8000.

## Production Checklist

1. Deploy and test in the private `Apolo_Dev` environment first.
2. Put HTTPS in front of port 8080. Never accept personal exports over plain public HTTP.
3. Keep the backend private; expose only the frontend reverse proxy.
4. Restrict network access to the intended users or add organization authentication at the reverse proxy.
5. Review the 1 GiB upload, temporary-filesystem, and 25-session limits for the target server. A large upload is temporarily spooled under `/tmp`; Compose provides a sparse 1 GiB memory-backed limit.
6. Monitor container health and memory consumption without logging uploaded contents.
7. Run the test and build commands from the README before release.
8. Keep `ENABLE_INSTAGRAPI_LAB=false`. The unofficial connector is intended only for short, local evaluations with a dedicated authorized account.

The included Compose configuration runs both containers without additional Linux capabilities, enables `no-new-privileges`, and uses read-only root filesystems with small temporary in-memory filesystems.

## Updating

```bash
git pull
docker compose build --pull
docker compose up -d
```

Follow Conventional Commits so release-please can maintain versions and `CHANGELOG.md`.
