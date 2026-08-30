"""Jersey Airport arrivals and departures from gov.je boards."""

from __future__ import annotations

from server.feeds.common import cached_load, panel, utc_now
from server.feeds.tables import parse_update_stamp, table_rows
from server.http_client import fetch_text

ARRIVALS_URL = "https://m.gov.je/airport/arrivals/"
DEPARTURES_URL = "https://m.gov.je/airport/departures/"
OFFICIAL_URL = "https://www.jerseyairport.com/flight/"
DISRUPTION_URL = "https://www.jerseyairport.com/flight/weather/"
SOURCE = "Jersey Airport"
TTL = 90

COLUMNS = ["scheduled", "flight", "location", "status"]


def _has_disruption(rows: list[dict]) -> str:
    cancelled = 0
    delayed = 0
    for row in rows:
        status = (row.get("status") or "").lower()
        if "cancel" in status:
            cancelled += 1
        elif any(word in status for word in ("delay", "estimated", "late")):
            delayed += 1
    if cancelled:
        return "red"
    if delayed:
        return "amber"
    return "green"


def _load() -> dict:
    arrivals_html = fetch_text(ARRIVALS_URL)
    departures_html = fetch_text(DEPARTURES_URL)
    arrivals = table_rows(arrivals_html, COLUMNS)
    departures = table_rows(departures_html, COLUMNS)
    stamp = parse_update_stamp(arrivals_html) or parse_update_stamp(departures_html)
    all_rows = arrivals + departures
    parsed = bool(arrivals or departures or stamp)
    if not parsed:
        return panel(
            status="unavailable",
            source=SOURCE,
            source_url=OFFICIAL_URL,
            data=None,
            extra={"reason": "Board HTML had no parseable flights"},
        )
    return panel(
        status="ok",
        source=SOURCE,
        source_url=OFFICIAL_URL,
        data={
            "arrivals": arrivals[:24],
            "departures": departures[:24],
            "boardUpdated": stamp,
            "disruption": _has_disruption(all_rows),
            "links": {"board": OFFICIAL_URL, "weather": DISRUPTION_URL},
        },
        updated_at=utc_now(),
    )


def get_airport() -> dict:
    return cached_load("airport", TTL, _load, source=SOURCE, source_url=OFFICIAL_URL)
