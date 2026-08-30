# UI

One screen, mobile-first. Calm ops-board look: dark navy and sea-fog, large status chips, no marketing chrome. v1 has no extra routes.

## Layout (top to bottom)

1. **Header** — app name, current UK clock, last full refresh, manual refresh.
2. **Risk strip** — one line: Green / Amber / Red plus a short reason, so disruption is visible before the tables.
3. **Jersey live hub** — 2×2 on desktop, stacked on mobile.
   - Weather: summary, max/min, wind (force + direction), rain, warning badge.
   - Airport EGJJ: compact arrivals/departures (scheduled vs status).
   - Harbour St Helier: vessel, from/to, status.
   - DFDS St Malo ↔ St Helier (featured): next outbound, next return, on-time / delayed / cancelled, link to DFDS updates.
4. **Cities** — four equal cards (Cape Town, Johannesburg, London, Santa Barbara): now, today high/low, short condition. Smaller type than Jersey.
5. **Rugby** — hero “Next on TV” (opponent, venue, countdown, UK kick-off, Sky Sports or ITV/ITVX). Below: upcoming list. Played matches dimmed. No heavy full-year grid in v1.

## Visual rules

- Status is never colour-only: also show the words Green, Amber, Red, On time, Delayed, Cancelled, Stale, Unavailable.
- Failure: muted panel, “Unavailable — view official source”, rest of the page keeps working.
- Every panel footer: source name, last updated, official link.
- Real headings, keyboard-focusable controls, contrast on the navy background.
- Phone-width first (360px), then widen the Jersey hub to two columns around 800px.

## Copy

- Jersey weather source label: **Jersey Met** (or **Open-Meteo (fallback)** if the Met feed is down).
- City cards: **Open-Meteo**.
- Rugby hero verb: **Watch on**.
