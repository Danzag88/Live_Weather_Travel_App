"""FastAPI app: dashboard + aggregated live feeds."""

from __future__ import annotations

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from server.feeds.airport import get_airport
from server.feeds.cities import get_cities
from server.feeds.dfds import get_dfds
from server.feeds.harbour import get_harbour
from server.feeds.jersey_weather import get_jersey_weather
from server.feeds.risk import derive_risk
from server.feeds.springboks import get_springboks

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"

app = FastAPI(title="Live Weather Travel", docs_url=None, redoc_url=None)
security = HTTPBasic(auto_error=False)


def require_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
) -> None:
    user = os.getenv("BASIC_AUTH_USER") or ""
    password = os.getenv("BASIC_AUTH_PASSWORD") or ""
    if not user or not password:
        return
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    user_ok = secrets.compare_digest(credentials.username, user)
    pass_ok = secrets.compare_digest(credentials.password, password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "publicBaseUrl": os.getenv("PUBLIC_BASE_URL") or None}


@app.get("/api/jersey")
def jersey(_: None = Depends(require_auth)) -> dict:
    with ThreadPoolExecutor(max_workers=4) as pool:
        weather_f = pool.submit(get_jersey_weather)
        airport_f = pool.submit(get_airport)
        harbour_f = pool.submit(get_harbour)
        dfds_f = pool.submit(get_dfds)
        weather = weather_f.result()
        airport = airport_f.result()
        harbour = harbour_f.result()
        dfds = dfds_f.result()
    return {
        "weather": weather,
        "airport": airport,
        "harbour": harbour,
        "dfds": dfds,
        "risk": derive_risk(weather, airport, dfds),
    }


@app.get("/api/cities")
def cities(_: None = Depends(require_auth)) -> dict:
    return get_cities()


@app.get("/api/springboks")
def springboks(_: None = Depends(require_auth)) -> dict:
    return get_springboks()


@app.get("/")
def index(_: None = Depends(require_auth)) -> FileResponse:
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=str(WEB)), name="static")
