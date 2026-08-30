"""Curated Springboks fixtures with UK local times."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from server.feeds.common import panel, utc_now

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "springboks.json"
UK = ZoneInfo("Europe/London")
SOURCE = "Curated fixtures"
SOURCE_URL = "https://www.sarugby.co.za/"


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _decorate(fixture: dict, now: datetime) -> dict:
    kickoff = _parse_utc(fixture["kickoffUtc"])
    uk_local = kickoff.astimezone(UK)
    played = kickoff < now
    return {
        **fixture,
        "kickoffUk": f"{uk_local.strftime('%a')} {uk_local.day} {uk_local.strftime('%b %Y, %H:%M %Z')}",
        "kickoffUkShort": f"{uk_local.strftime('%a')} {uk_local.day} {uk_local.strftime('%b, %H:%M')}",
        "played": played,
        "watchOn": fixture.get("ukBroadcaster"),
    }


def get_springboks() -> dict:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    fixtures = [_decorate(item, now) for item in raw.get("fixtures", [])]
    fixtures.sort(key=lambda item: item["kickoffUtc"])
    next_match = next((item for item in fixtures if not item["played"]), None)
    return panel(
        status="ok",
        source=SOURCE,
        source_url=SOURCE_URL,
        data={
            "next": next_match,
            "fixtures": fixtures,
            "rightsMap": raw.get("rightsMap", {}),
        },
        updated_at=utc_now(),
    )
