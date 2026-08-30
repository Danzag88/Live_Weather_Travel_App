"""Shared panel shape and cached load helper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from server.cache import cache

logger = logging.getLogger("feeds")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def panel(
    *,
    status: str,
    source: str,
    source_url: str,
    data: Any | None,
    updated_at: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": status,
        "updatedAt": updated_at or utc_now(),
        "source": source,
        "sourceUrl": source_url,
        "data": data,
    }
    if extra:
        body.update(extra)
    return body


def unavailable(source: str, source_url: str, reason: str | None = None) -> dict[str, Any]:
    extra = {"reason": reason} if reason else None
    return panel(
        status="unavailable",
        source=source,
        source_url=source_url,
        data=None,
        extra=extra,
    )


def cached_load(
    key: str,
    ttl_seconds: float,
    loader: Callable[[], dict[str, Any]],
    *,
    source: str,
    source_url: str,
) -> dict[str, Any]:
    fresh = cache.get_fresh(key)
    if fresh is not None:
        return fresh
    try:
        result = loader()
        if result.get("status") == "ok":
            cache.set(key, result, ttl_seconds)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Feed %s failed: %s", key, exc)
        last = cache.get_last(key)
        if last is not None:
            stale = dict(last)
            stale["status"] = "stale"
            return stale
        return unavailable(source, source_url, reason=str(exc))
