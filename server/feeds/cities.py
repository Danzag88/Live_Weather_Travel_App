"""Open-Meteo forecasts for the four secondary cities."""

from __future__ import annotations

from urllib.parse import urlencode

from server.feeds.common import cached_load, panel, utc_now
from server.http_client import fetch_json

CITIES = [
    {
        "id": "cape-town",
        "name": "Cape Town",
        "latitude": -33.9249,
        "longitude": 18.4241,
        "timezone": "Africa/Johannesburg",
    },
    {
        "id": "johannesburg",
        "name": "Johannesburg",
        "latitude": -26.2041,
        "longitude": 28.0473,
        "timezone": "Africa/Johannesburg",
    },
    {
        "id": "london",
        "name": "London",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timezone": "Europe/London",
    },
    {
        "id": "santa-barbara",
        "name": "Santa Barbara",
        "latitude": 34.4208,
        "longitude": -119.6982,
        "timezone": "America/Los_Angeles",
    },
]

SOURCE = "Open-Meteo"
SOURCE_URL = "https://open-meteo.com/"
TTL = 15 * 60

WMO = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Rain showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with hail",
}


def weather_label(code: int | None) -> str:
    if code is None:
        return "—"
    return WMO.get(int(code), f"Code {code}")


def _forecast_url(city: dict) -> str:
    query = urlencode(
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": city["timezone"],
            "forecast_days": 2,
            "wind_speed_unit": "mph",
        }
    )
    return f"https://api.open-meteo.com/v1/forecast?{query}"


def _one_city(city: dict) -> dict:
    payload = fetch_json(_forecast_url(city))
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected Open-Meteo response")
    current = payload.get("current") or {}
    daily = payload.get("daily") or {}
    code = current.get("weather_code")
    return {
        "id": city["id"],
        "name": city["name"],
        "timezone": city["timezone"],
        "temperatureC": current.get("temperature_2m"),
        "condition": weather_label(code),
        "weatherCode": code,
        "windMph": current.get("wind_speed_10m"),
        "windDirection": current.get("wind_direction_10m"),
        "precipitationMm": current.get("precipitation"),
        "highC": _first(daily.get("temperature_2m_max")),
        "lowC": _first(daily.get("temperature_2m_min")),
        "rainChancePct": _first(daily.get("precipitation_probability_max")),
    }


def _first(values: object) -> object:
    if isinstance(values, list) and values:
        return values[0]
    return None


def _load() -> dict:
    cities = [_one_city(city) for city in CITIES]
    return panel(
        status="ok",
        source=SOURCE,
        source_url=SOURCE_URL,
        data={"cities": cities},
        updated_at=utc_now(),
    )


def get_cities() -> dict:
    return cached_load(
        "cities", TTL, _load, source=SOURCE, source_url=SOURCE_URL
    )
