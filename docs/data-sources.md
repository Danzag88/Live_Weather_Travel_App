# Data sources and access rules

Prefer official pages and documented APIs. Fetch only from the server. Do not scrape in the browser. Cache so a deployed tab that auto-refreshes does not look like a bot.

**User-Agent:** `LiveWeatherTravelApp/1.0 (personal dashboard; +https://github.com/Danzag88/Live_Weather_Travel_App)`

If a site blocks reuse or HTML changes, stop parsing that feed and link out to the official page.

## Jersey weather (primary)

| Need | Official source | Access | Cache |
| --- | --- | --- | --- |
| Public forecast | [Jersey Met](https://www.gov.je/weather/) | Link + optional unofficial JSON | 10 min |
| Warnings | [CI weather warnings](https://www.gov.je/weather/ciweatherwarnings/) | Link (no public API) | — |
| Shipping / sea state | [Channel Islands shipping forecast](https://www.gov.je/weather/shipping/) | Link | — |
| Tides (St Helier) | [Jersey Met tide times](https://www.gov.je/weather/tidetimes/) | Link | — |
| Aviation METAR/TAF | [NOAA AWC](https://aviationweather.gov/data/api/) station **EGJJ**; also [Jersey Met aviation](https://www.gov.je/weather/aviation/) | Documented NOAA JSON | 5 min |

There is no documented Jersey Met forecast API. An unofficial blob at `prodgojweatherstorage.blob.core.windows.net` may be used if it responds; treat it as breakable. Label **Jersey Met** as the source of truth. Use Open-Meteo for St Helier only as a labelled fallback.

## Jersey Airport

- [Flight boards](https://www.jerseyairport.com/flight/)
- [gov.je arrivals](https://m.gov.je/airport/arrivals/) and departures
- [Weather disruption](https://www.jerseyairport.com/flight/weather/)

No public API. Server-side HTML fetch + parse. Cache **90 seconds**. If parsing fails, show “Open official board” only.

## Ports of Jersey (St Helier)

- [Arrivals and departures](https://www.ports.je/jerseyharbours/arrivals-departures/)
- [Harbour arrivals](https://m.gov.je/harbour/arrivals) / [departures](https://m.gov.je/Harbour/Departures)

Operators supply the times. Same access as the airport. Cache **90 seconds**.

## DFDS — Saint Malo ↔ St Helier

- [Route page](https://www.dfds.com/en-gb/passenger-ferries/ferry-crossings/ferries-to-jersey/st-malo-jersey)
- [Live travel updates](https://www.dfds.com/en-gb/passenger-ferries/passenger-information/travel-updates)

No public API. Server-side fetch of travel updates. Cache **90 seconds**. Always link out. The DFDS page is often JavaScript-rendered; if no Jersey disruption text is present, the panel is **unavailable** and shows the official updates link. Mention Poole / Portsmouth only as fallback copy when St Malo is cancelled; do not scrape those routes in v1.

## Four cities

[Open-Meteo forecast API](https://open-meteo.com/) (documented, no key). Cache **15 minutes**.

| City | Latitude | Longitude | Timezone |
| --- | --- | --- | --- |
| Cape Town | −33.9249 | 18.4241 | Africa/Johannesburg |
| Johannesburg | −26.2041 | 28.0473 | Africa/Johannesburg |
| London | 51.5074 | −0.1278 | Europe/London |
| Santa Barbara, CA | 34.4208 | −119.6982 | America/Los_Angeles |

Badge the source **Open-Meteo**. Do not present these cards as Jersey Met.

## Springboks

No reliable “what channel is this on?” API. Use curated [`data/springboks.json`](../data/springboks.json): `kickoffUtc`, teams, venue, competition, `ukBroadcaster`, channels, stream.

**UK rights map (2026, as documented at build time)**

- SANZAAR / Rugby’s Greatest Rivalry → **Sky Sports** (Action / Sky Sports+ / Sky Go / NOW)
- Nations Championship 2026 → **ITV / ITVX** (exact ITV1 vs ITV4 only when weekly listings are known)

Confirm the Australia vs South Africa (Perth) listing closer to the day.

## Legal and reliability

- Attribute every panel. Respect robots.txt and terms of use.
- Timeouts 5–8 seconds, one retry. One dead feed must not block the rest of `/api/jersey`.
- Rate limits assume personal use: one deployed instance, not a public traffic spike.
