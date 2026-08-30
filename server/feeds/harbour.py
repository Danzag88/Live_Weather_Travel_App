"""Ports of Jersey harbour arrivals and departures."""

from __future__ import annotations

from server.feeds.common import cached_load, panel, utc_now
from server.feeds.tables import parse_update_stamp, table_rows
from server.http_client import fetch_text

ARRIVALS_URL = "https://m.gov.je/harbour/arrivals"
DEPARTURES_URL = "https://m.gov.je/Harbour/Departures"
OFFICIAL_URL = "https://www.ports.je/jerseyharbours/arrivals-departures/"
SOURCE = "Ports of Jersey"
TTL = 90


def _load() -> dict:
    arrivals_html = fetch_text(ARRIVALS_URL)
    departures_html = fetch_text(DEPARTURES_URL)
    arrival_cols = ["vessel", "origin", "quay", "sta", "status"]
    departure_cols = ["vessel", "destination", "quay", "std", "status"]
    arrivals = table_rows(arrivals_html, arrival_cols)
    if not arrivals:
        arrivals = table_rows(arrivals_html, ["scheduled", "vessel", "origin", "status"])
    departures = table_rows(departures_html, departure_cols)
    if not departures:
        departures = table_rows(
            departures_html, ["scheduled", "vessel", "destination", "status"]
        )
    stamp = parse_update_stamp(arrivals_html) or parse_update_stamp(departures_html)
    if not arrivals and not departures and not stamp:
        ports_html = fetch_text(OFFICIAL_URL)
        arrivals = table_rows(ports_html, arrival_cols)
        departures = table_rows(ports_html, departure_cols)
        stamp = parse_update_stamp(ports_html)
        if not arrivals and not departures and not stamp:
            return panel(
                status="unavailable",
                source=SOURCE,
                source_url=OFFICIAL_URL,
                data=None,
                extra={"reason": "Harbour HTML had no parseable movements"},
            )
    return panel(
        status="ok",
        source=SOURCE,
        source_url=OFFICIAL_URL,
        data={
            "arrivals": arrivals[:20],
            "departures": departures[:20],
            "boardUpdated": stamp,
            "note": "Times are supplied by shipping operators.",
        },
        updated_at=utc_now(),
    )


def get_harbour() -> dict:
    return cached_load("harbour", TTL, _load, source=SOURCE, source_url=OFFICIAL_URL)
