"""Derive Jersey travel risk from weather, airport, and DFDS panels."""

from __future__ import annotations


def _force_from_weather(weather: dict) -> int:
    data = weather.get("data") or {}
    forecast = data.get("forecast") or {}
    raw = forecast.get("windForce")
    if not raw:
        return 0
    text = str(raw).upper().replace("F", "").strip()
    try:
        return int(text.split()[0])
    except (TypeError, ValueError):
        return 0


def derive_risk(weather: dict, airport: dict, dfds: dict) -> dict:
    reasons: list[str] = []
    level = "green"

    dfds_data = dfds.get("data") or {}
    sailing = (dfds_data.get("sailingStatus") or "").lower()
    if sailing == "cancelled" or dfds_data.get("disrupted") and sailing == "cancelled":
        level = "red"
        reasons.append("DFDS Saint Malo ↔ St Helier is cancelled.")
    elif sailing == "delayed":
        level = "amber"
        reasons.append("DFDS reports delays or disruption.")
    elif dfds.get("status") == "unavailable":
        reasons.append("DFDS live text could not be read — check the official updates.")

    airport_data = airport.get("data") or {}
    disruption = airport_data.get("disruption")
    if disruption == "red":
        level = "red"
        reasons.append("Airport board shows cancelled flights.")
    elif disruption == "amber" and level != "red":
        level = "amber"
        reasons.append("Airport board shows delays.")

    force = _force_from_weather(weather)
    warning = (weather.get("data") or {}).get("warning")
    if force >= 7:
        level = "red"
        reasons.append(warning or f"Wind force {force}.")
    elif force >= 5 and level != "red":
        if level == "green":
            level = "amber"
        reasons.append(warning or f"Fresh or strong wind (F{force}).")
    elif warning and level == "green":
        level = "amber"
        reasons.append(warning)

    if not reasons:
        reasons.append("No warnings on the cached feeds. Confirm official boards before travel.")

    return {"level": level, "summary": " ".join(reasons)}
