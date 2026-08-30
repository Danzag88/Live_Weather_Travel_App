# Architecture

Vanilla HTML/CSS/JS dashboard served by a small FastAPI process. The browser talks only to same-origin `/api/*`. Third-party feeds are fetched, cached, and summarised on the server.

```
/
  docs/                  # this folder
  data/springboks.json   # curated fixtures + UK TV
  server/main.py         # FastAPI app
  server/cache.py        # in-memory TTL cache
  server/http_client.py  # shared User-Agent, timeout, retry
  server/feeds/          # jersey_weather, airport, harbour, dfds, cities, springboks
  web/index.html
  web/styles.css
  web/app.js
  .env.example
```

## Runtime

- FastAPI serves `/` (static dashboard) and `/api/*` (JSON).
- In-memory cache per feed. On fetch failure, return `status: "stale"` with the last good payload, or `status: "unavailable"` with no payload.
- Display timezone: `Europe/London`. Rugby kick-offs stored as UTC; the client formats them.
- Jersey APIs refresh on a 90s browser timer. Cities every 15 minutes. Rugby on load and manual refresh.
- Optional `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` protect the whole site when deployed.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard HTML |
| GET | `/api/health` | Process liveness |
| GET | `/api/jersey` | Weather, airport, harbour, DFDS (each independently filled) |
| GET | `/api/cities` | Four-city Open-Meteo forecasts |
| GET | `/api/springboks` | Next match + full fixture list |

### `/api/jersey` shape

Each child is `{ "status": "ok" | "stale" | "unavailable", "updatedAt": "...", "source": "...", "sourceUrl": "...", "data": ... | null }`.

The API also returns `risk`: `{ "level": "green" | "amber" | "red", "summary": "..." }` derived from weather warnings plus airport and DFDS status.

### `/api/springboks` shape

`{ "next": <fixture|null>, "fixtures": [...], "generatedAt": "..." }`. Each fixture includes `kickoffUtc` and preformatted `kickoffUk`.

## Cache TTLs

- Airport, harbour, DFDS: 90 seconds
- METAR/TAF: 5 minutes
- Jersey forecast (unofficial JSON or Open-Meteo fallback): 10 minutes
- Cities: 15 minutes
- Springboks file: read from disk on each request (small, curated)

## Deploy

One service (Render, Fly, or Railway). See [deployment.md](deployment.md).
