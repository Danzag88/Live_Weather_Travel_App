# Requirements (v1)

Personal live-ops dashboard for Jersey travel, four city forecasts, and Springboks fixtures on UK television.

## In scope

- **Jersey live hub** is the primary surface: Jersey Met weather, warnings, shipping and tides, Jersey Airport (EGJJ), Ports of Jersey harbour movements, and DFDS **Saint Malo ↔ St Helier**.
- **Secondary forecast cards only:** Cape Town, Johannesburg, London, Santa Barbara (USA).
- **Springboks men’s Tests:** date, UK time (`Europe/London`), venue, competition, UK broadcaster and stream.
- Personal deployed site: one user, reachable from anywhere. No public SEO, no multi-user accounts. Optional HTTP basic auth so a public URL is not an open board.
- Auto-refresh: Jersey live panels every 90 seconds; city forecasts every 15 minutes; rugby calendar on page load (plus a manual refresh).
- Every panel shows **source name**, **last updated**, and a link to the official page.

## Out of scope (v1)

Trip planning, destination search, travel dates, user accounts, push notifications, and native apps stay future work.

## Non-functional

- All secrets stay server-side. The browser never calls third-party APIs.
- If a feed fails, show the last cached value (`stale`) or a clear **unavailable** state plus the official link. Never blank the whole page.
- Display times in UK local time. Store rugby kick-offs as UTC.
- Identify outbound HTTP with a polite `User-Agent`. Timeouts 5–8 seconds, one retry. Cache aggressively.

## Success criteria

- Opening `/` shows Jersey risk, weather, airport, harbour, DFDS, four cities, and the next Springbok on TV.
- A dead airport or ferry feed does not hide weather, cities, or rugby.
- Kick-off times switch correctly between BST and GMT via `Europe/London`.
