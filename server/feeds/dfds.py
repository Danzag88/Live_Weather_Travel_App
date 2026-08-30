"""DFDS Saint Malo ↔ St Helier travel updates (best-effort HTML)."""

from __future__ import annotations

from bs4 import BeautifulSoup

from server.feeds.common import cached_load, panel, utc_now
from server.http_client import fetch_text

UPDATES_URL = (
    "https://www.dfds.com/en-gb/passenger-ferries/passenger-information/travel-updates"
)
ROUTE_URL = (
    "https://www.dfds.com/en-gb/passenger-ferries/ferry-crossings/ferries-to-jersey/st-malo-jersey"
)
SOURCE = "DFDS"
TTL = 90

ROUTE_WORDS = (
    "jersey",
    "st helier",
    "st. helier",
    "st malo",
    "st. malo",
    "saint malo",
    "st-malo",
)
DISRUPT_WORDS = ("cancel", "delay", "disrupt", "suspended", "divert")


def _looks_like_nav(text: str) -> bool:
    low = text.lower()
    if low.count("ferries") >= 3:
        return True
    if "routes ferries from" in low or "all ferry routes" in low:
        return True
    if "passenger ferries freight" in low:
        return True
    return False


def _snippets(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    seen: set[str] = set()
    for tag in soup.find_all(["p", "li", "h2", "h3", "h4", "article"]):
        text = tag.get_text(" ", strip=True)
        if len(text) < 40 or len(text) > 600:
            continue
        if _looks_like_nav(text):
            continue
        low = text.lower()
        if not any(word in low for word in ROUTE_WORDS):
            continue
        if not any(word in low for word in DISRUPT_WORDS):
            continue
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        found.append(text)
        if len(found) >= 6:
            break
    return found


def _status_from_snippets(snippets: list[str]) -> str:
    blob = " ".join(snippets).lower()
    if any(word in blob for word in ("cancel", "suspended")):
        return "cancelled"
    if any(word in blob for word in ("delay", "disrupt")):
        return "delayed"
    if snippets:
        return "updates"
    return "unknown"


def _load() -> dict:
    html = fetch_text(UPDATES_URL)
    snippets = _snippets(html)
    if not snippets:
        route_html = fetch_text(ROUTE_URL)
        snippets = _snippets(route_html)
    sailing_status = _status_from_snippets(snippets)
    disrupted = sailing_status in {"cancelled", "delayed"}
    return panel(
        status="ok" if snippets else "unavailable",
        source=SOURCE,
        source_url=UPDATES_URL,
        data={
            "route": "Saint Malo ↔ St Helier",
            "sailingStatus": sailing_status,
            "updates": snippets,
            "fallbackRoutes": (
                ["Poole–Jersey", "Portsmouth–Jersey"] if sailing_status == "cancelled" else []
            ),
            "links": {"updates": UPDATES_URL, "route": ROUTE_URL},
            "disrupted": disrupted,
        }
        if snippets
        else None,
        updated_at=utc_now(),
        extra={"reason": None if snippets else "No Jersey text on DFDS updates page"},
    )


def get_dfds() -> dict:
    return cached_load("dfds", TTL, _load, source=SOURCE, source_url=UPDATES_URL)
