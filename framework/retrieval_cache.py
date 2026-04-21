"""Disk-backed retrieval cache for repeatable local query results.

Keys cache entries by sha256 hash of (query_text, top_k). Stores result dicts
as JSON files under artifacts/retrieval_cache/. Caller owns serialization of
RetrievalResult into a plain dict.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.context_retrieval import RetrievalResult

# -- import-time assertion --
assert dataclasses.is_dataclass(RetrievalResult), "INTERFACE MISMATCH: RetrievalResult must be a dataclass"

_DEFAULT_CACHE_DIR = Path("artifacts") / "retrieval_cache"
_DEFAULT_TTL_SECONDS = 3600


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cache_key(query_text: str, top_k: int) -> str:
    raw = json.dumps({"query_text": query_text, "top_k": top_k}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class CachedRetrievalResult:
    cache_key: str
    query_text: str
    top_k: int
    result_dict: dict[str, Any]
    cached_at: str
    ttl_seconds: int = _DEFAULT_TTL_SECONDS

    def is_expired(self) -> bool:
        cached = datetime.fromisoformat(self.cached_at)
        now = datetime.now(timezone.utc)
        delta = (now - cached).total_seconds()
        return delta > self.ttl_seconds


class RetrievalCache:
    def __init__(
        self,
        *,
        cache_dir: Optional[Path] = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        self._dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._ttl = ttl_seconds

    def _path_for(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, query_text: str, top_k: int) -> Optional[CachedRetrievalResult]:
        """Return cached result or None if missing/expired."""
        key = _cache_key(query_text, top_k)
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entry = CachedRetrievalResult(**data)
            if entry.is_expired():
                return None
            return entry
        except Exception:
            return None

    def put(self, query_text: str, top_k: int, result_dict: dict[str, Any]) -> CachedRetrievalResult:
        """Store result_dict under the derived cache key."""
        key = _cache_key(query_text, top_k)
        entry = CachedRetrievalResult(
            cache_key=key,
            query_text=query_text,
            top_k=top_k,
            result_dict=result_dict,
            cached_at=_iso_now(),
            ttl_seconds=self._ttl,
        )
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(key)
        path.write_text(
            json.dumps(dataclasses.asdict(entry), ensure_ascii=False),
            encoding="utf-8",
        )
        return entry

    def invalidate(self, query_text: str, top_k: int) -> bool:
        """Delete cache entry. Returns True if deleted, False if not present."""
        key = _cache_key(query_text, top_k)
        path = self._path_for(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Delete all cache files. Returns count of deleted files."""
        if not self._dir.exists():
            return 0
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink()
            count += 1
        return count

    def stats(self) -> dict[str, Any]:
        """Return basic cache statistics."""
        if not self._dir.exists():
            return {"total_entries": 0, "cache_dir": str(self._dir)}
        entries = list(self._dir.glob("*.json"))
        return {
            "total_entries": len(entries),
            "cache_dir": str(self._dir),
        }


__all__ = [
    "CachedRetrievalResult",
    "RetrievalCache",
]
