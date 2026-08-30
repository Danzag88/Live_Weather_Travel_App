"""Shared outbound HTTP: polite User-Agent, timeout, one retry."""

from __future__ import annotations

import logging

import httpx

USER_AGENT = (
    "LiveWeatherTravelApp/1.0 (personal dashboard; "
    "+https://github.com/Danzag88/Live_Weather_Travel_App)"
)
TIMEOUT = httpx.Timeout(8.0, connect=5.0)

logger = logging.getLogger("feeds")


def get_client() -> httpx.Client:
    return httpx.Client(
        timeout=TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    )


def fetch_text(url: str, *, extra_headers: dict[str, str] | None = None) -> str:
    headers = extra_headers or {}
    last_error: Exception | None = None
    with get_client() as client:
        for attempt in range(2):
            try:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001 — one retry then caller handles
                last_error = exc
                logger.warning("GET %s failed (attempt %s): %s", url, attempt + 1, exc)
    raise last_error or RuntimeError(f"GET {url} failed")


def fetch_json(url: str, *, extra_headers: dict[str, str] | None = None) -> object:
    headers = {"Accept": "application/json", **(extra_headers or {})}
    last_error: Exception | None = None
    with get_client() as client:
        for attempt in range(2):
            try:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("GET %s failed (attempt %s): %s", url, attempt + 1, exc)
    raise last_error or RuntimeError(f"GET {url} failed")
