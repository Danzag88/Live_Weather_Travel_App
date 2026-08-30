# Deployment

Personal instance, reachable from your phone. One process serves the dashboard and the API.

## Environment

Copy `.env.example` to `.env` locally. On a host, set the same variables in the service dashboard.

| Variable | Required | Purpose |
| --- | --- | --- |
| `PORT` | Host-provided | Listen port (default `8000` locally) |
| `BASIC_AUTH_USER` | No | If set with password, require HTTP basic auth |
| `BASIC_AUTH_PASSWORD` | No | Pair with user |
| `PUBLIC_BASE_URL` | No | Used only in logs / health |

Never commit `.env`.

## Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Host (pick one)

**Render:** Web Service, build `pip install -r requirements.txt`, start `uvicorn server.main:app --host 0.0.0.0 --port $PORT`. Set basic auth env vars.

**Fly.io:** `fly launch` using the included `Dockerfile` and `fly.toml`. Set secrets: `fly secrets set BASIC_AUTH_USER=... BASIC_AUTH_PASSWORD=...`

**Railway:** New service from this repo, start command the same as Render.

## Phone

After deploy, add the HTTPS URL to the home screen. If basic auth is on, the browser will prompt once.

## Health

`GET /api/health` is unauthenticated and should return `{ "ok": true }`. Use it as the host health check so basic auth does not fail probes.
