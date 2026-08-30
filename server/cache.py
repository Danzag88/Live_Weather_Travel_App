"""In-memory TTL cache with last-good payload for stale responses."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    stored_at: float
    ttl_seconds: float

    def is_fresh(self) -> bool:
        return (time.time() - self.stored_at) < self.ttl_seconds


class TtlCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[str, CacheEntry] = {}

    def get_fresh(self, key: str) -> Any | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry and entry.is_fresh():
                return entry.value
            return None

    def get_last(self, key: str) -> Any | None:
        with self._lock:
            entry = self._entries.get(key)
            return entry.value if entry else None

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        with self._lock:
            self._entries[key] = CacheEntry(
                value=value, stored_at=time.time(), ttl_seconds=ttl_seconds
            )


cache = TtlCache()
