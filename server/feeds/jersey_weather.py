"""Jersey Met forecast (optional unofficial JSON), METAR EGJJ, Open-Meteo fallback."""

from __future__ import annotations

from urllib.parse import urlencode

from server.feeds.cities import weather_label
from server.feeds.common import cached_load, panel, utc_now
from server.http_client import fetch_json

JERSEY_MET_URL = "https://www.gov.je/weather/"
JERSEY_WARNINGS_URL = "https://www.gov.je/weather/ciweatherwarnings/"
JERSEY_SHIPPING_URL = "https://www.gov.je/weather/shipping/"
JERSEY_TIDES_URL = "https://www.gov.je/weather/tidetimes/"
JERSEY_AVIATION_URL = "https://www.gov.je/weather/aviation/"
JERSEY_FORECAST_JSON = (
    "https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json"
)
METAR_URL = "https://aviationweather.gov/api/data/metar?ids=EGJJ&format=json"
TAF_URL = "https://aviationweather.gov/api/data/taf?ids=EGJJ&format=json"

ST_HELIER = {"latitude": 49.1858, "longitude": -2.1100}

LINKS = {
    "forecast": JERSEY_MET_URL,
    "warnings": JERSEY_WARNINGS_URL,
    "shipping": JERSEY_SHIPPING_URL,
    "tides": JERSEY_TIDES_URL,
    "aviation": JERSEY_AVIATION_URL,
}


def _metar() -> dict | None:
    payload = fetch_json(METAR_URL)
    if not isinstance(payload, list) or not payload:
        return None
    row = payload[0]
    if not isinstance(row, dict):
        return None
    return {
        "raw": row.get("rawOb"),
        "tempC": row.get("temp"),
        "dewpointC": row.get("dewp"),
        "windDir": row.get("wdir"),
        "windKt": row.get("wspd"),
        "visibility": row.get("visib"),
        "cover": row.get("cover"),
        "flightCategory": row.get("fltCat"),
        "observedAt": row.get("reportTime"),
    }


def _taf() -> dict | None:
    payload = fetch_json(TAF_URL)
    if not isinstance(payload, list) or not payload:
        return None
    row = payload[0]
    if not isinstance(row, dict):
        return None
    return {"raw": row.get("rawTAF"), "issuedAt": row.get("issueTime")}


def _jersey_met_forecast() -> dict | None:
    payload = fetch_json(JERSEY_FORECAST_JSON)
    if not isinstance(payload, dict):
        return None
    days = payload.get("forecastDay") or []
    today = days[0] if days else {}
    outlook = []
    for day in days[:5]:
        outlook.append(
            {
                "name": day.get("dayName"),
                "summary": day.get("summary") or day.get("dayToolTip"),
                "maxTemp": day.get("maxTemp"),
                "minTemp": day.get("minTemp"),
                "wind": day.get("windToolTipMPH") or day.get("windDescription"),
                "rainChancePct": _rain_chance(day),
            }
        )
    return {
        "provider": "Jersey Met",
        "issued": payload.get("forecastTime") or payload.get("issuetime"),
        "currentTemp": payload.get("currentTemprature"),
        "period": payload.get("morningEvening") or today.get("dayName"),
        "summary": today.get("summary") or today.get("nightDescripiton"),
        "morning": today.get("morningDescripiton"),
        "afternoon": today.get("afternoonDescripiton"),
        "night": today.get("nightDescripiton"),
        "maxTemp": today.get("maxTemp"),
        "minTemp": today.get("minTemp"),
        "wind": today.get("windToolTipMPH")
        or today.get("afternoonWindDescripiton")
        or today.get("windDescription"),
        "windForce": today.get("windSpeed") or today.get("windSpeedForceAfternoon"),
        "windDirection": today.get("windDirection")
        or today.get("windDirectionAfternoon"),
        "rainChancePct": _rain_chance(today),
        "uvIndex": today.get("uvIndex"),
        "frost": today.get("frost") or None,
        "outlook": outlook,
    }


def _rain_chance(day: dict) -> int | None:
    values = []
    for key in ("rainProbMorning", "rainProbAfternoon", "rainProbEvening"):
        raw = day.get(key)
        if raw in (None, ""):
            continue
        try:
            values.append(int(raw))
        except (TypeError, ValueError):
            continue
    return max(values) if values else None


def _open_meteo_fallback() -> dict:
    query = urlencode(
        {
            "latitude": ST_HELIER["latitude"],
            "longitude": ST_HELIER["longitude"],
            "current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Europe/London",
            "forecast_days": 3,
            "wind_speed_unit": "mph",
        }
    )
    payload = fetch_json(f"https://api.open-meteo.com/v1/forecast?{query}")
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected Open-Meteo response")
    current = payload.get("current") or {}
    daily = payload.get("daily") or {}
    code = current.get("weather_code")
    return {
        "provider": "Open-Meteo (fallback)",
        "issued": None,
        "currentTemp": _fmt_temp(current.get("temperature_2m")),
        "period": "Now",
        "summary": weather_label(code),
        "morning": None,
        "afternoon": None,
        "night": None,
        "maxTemp": _fmt_temp(_first(daily.get("temperature_2m_max"))),
        "minTemp": _fmt_temp(_first(daily.get("temperature_2m_min"))),
        "wind": _fmt_wind(current.get("wind_speed_10m"), current.get("wind_direction_10m")),
        "windForce": None,
        "windDirection": current.get("wind_direction_10m"),
        "rainChancePct": _first(daily.get("precipitation_probability_max")),
        "uvIndex": None,
        "frost": None,
        "outlook": [],
    }


def _fmt_temp(value: object) -> str | None:
    if value is None:
        return None
    return f"{round(float(value))}°C"


def _fmt_wind(speed: object, direction: object) -> str | None:
    if speed is None:
        return None
    if direction is None:
        return f"{round(float(speed))} mph"
    return f"{round(float(speed))} mph from {int(direction)}°"


def _first(values: object) -> object:
    if isinstance(values, list) and values:
        return values[0]
    return None


def _force_number(force: object) -> int | None:
    if not force:
        return None
    text = str(force).upper().replace("F", "").strip()
    try:
        return int(text.split()[0])
    except (TypeError, ValueError):
        return None


def _load() -> dict:
    forecast = None
    provider = "Jersey Met"
    try:
        forecast = _jersey_met_forecast()
    except Exception:
        forecast = None
    if not forecast:
        forecast = _open_meteo_fallback()
        provider = forecast["provider"]

    metar = None
    taf = None
    try:
        metar = _metar()
    except Exception:
        metar = None
    try:
        taf = _taf()
    except Exception:
        taf = None

    warning = None
    force = _force_number(forecast.get("windForce"))
    if force is not None and force >= 6:
        warning = f"Strong wind {forecast.get('windForce')} — check ferry and airport."
    elif force is not None and force >= 5:
        warning = f"Fresh wind {forecast.get('windForce')} — disruption possible."

    data = {
        "forecast": forecast,
        "metar": metar,
        "taf": taf,
        "warning": warning,
        "links": LINKS,
    }
    return panel(
        status="ok",
        source=provider,
        source_url=JERSEY_MET_URL,
        data=data,
        updated_at=utc_now(),
    )


def get_jersey_weather() -> dict:
    source = "Jersey Met"
    return cached_load(
        "jersey-weather",
        10 * 60,
        _load,
        source=source,
        source_url=JERSEY_MET_URL,
    )
