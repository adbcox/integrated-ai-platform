"""Plane ingester — modules + issues + tracked_in entity_links.

Read-only mirror of the Plane project (ADR-A-006: xindex consumes
Plane state but never writes back). We pull modules and issues via
the V1 REST API, denormalize state UUID → state name and the first
module reference, and emit `tracked_in` entity_links from local
artifacts (ADRs and deliverables) to their Plane issue when the
issue's `external_id` matches:

    'ADR-A-NNN'         → from_kind='adr',         from_ref='ADR-A-NNN'
    'D-NN-MM[.x]'       → from_kind='deliverable', from_ref='D-NN-MM[.x]'
    'Phase-NN'          → from_kind='phase',       from_ref='Phase-NN'

Doctrine:
  - NEVER raises. RateLimitError, network errors, missing token →
    return ok=False; the orchestrator restores from snapshot.
  - 60 req/min Plane CE limit: a single token, paginated GETs
    (page_size=100), no parallel requests; modest extra read budget
    well under the limit for a project of our size.
  - Token comes from /run/secrets/plane-credentials.env (rendered
    by the vault-agent-xindex sidecar). Never logged.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:  # pragma: no cover — runtime dep, optional in unit tests with stub fetcher
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


CREDENTIALS_PATH = Path(
    os.environ.get(
        "XINDEX_PLANE_CREDENTIALS",
        "/run/secrets/plane-credentials.env",
    )
)

# Mirrors framework/plane_connector.py's RateLimitError but kept
# local: this ingester never imports framework code (ADR-A-006).
class _RateLimitError(Exception):
    pass


@dataclass
class PlaneIngestResult:
    ok: bool
    plane_issues: int = 0
    plane_modules: int = 0
    entity_links: int = 0
    error: str = ""
    skipped: bool = False
    skip_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "plane_issues": self.plane_issues,
            "plane_modules": self.plane_modules,
            "entity_links": self.entity_links,
            "error": self.error,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


def _read_creds() -> dict[str, str] | None:
    """Return {'token','url','workspace','project_id'} or None if any missing."""
    out: dict[str, str] = {}
    env_keys = {
        "PLANE_API_TOKEN": "token",
        "PLANE_URL": "url",
        "PLANE_WORKSPACE": "workspace",
        "PLANE_PROJECT_ID": "project_id",
    }
    for k, target in env_keys.items():
        v = os.environ.get(k)
        if v:
            out[target] = v

    if CREDENTIALS_PATH.is_file():
        try:
            for line in CREDENTIALS_PATH.read_text().splitlines():
                if "=" not in line or line.startswith("#"):
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k in env_keys and env_keys[k] not in out:
                    out[env_keys[k]] = v
        except OSError:
            pass

    if not all(out.get(t) for t in env_keys.values()):
        return None
    return out


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


# ── Default fetcher (real Plane API) ────────────────────────────────

def _default_fetcher(creds: dict[str, str]) -> tuple[list[dict], list[dict], list[dict]] | None:
    """Return (modules, states, issues) or None on failure.

    Translates 429 → _RateLimitError; any other failure returns None
    so the ingester surfaces a generic error.
    """
    if requests is None:
        return None
    base = creds["url"].rstrip("/")
    ws = creds["workspace"]
    proj = creds["project_id"]
    sess = requests.Session()
    sess.headers.update({
        "X-Api-Key": creds["token"],
        "Content-Type": "application/json",
    })

    def _get(path: str, params: dict | None = None) -> Any:
        url = f"{base}/api/v1/workspaces/{ws}/projects/{proj}{path}"
        r = sess.get(url, params=params, timeout=15)
        if r.status_code == 429:
            raise _RateLimitError(f"429 on {path}")
        r.raise_for_status()
        return r.json() if r.content else {}

    def _paged(path: str) -> list[dict]:
        out: list[dict] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"per_page": 100}
            if cursor:
                params["cursor"] = cursor
            data = _get(path, params=params)
            if isinstance(data, dict):
                results = data.get("results", []) or []
                out.extend(results)
                next_page = data.get("next_page_results")
                count = data.get("count")
                if next_page is False or count == 0 or not results:
                    break
                cursor = data.get("next_cursor")
                if not cursor:
                    break
            else:
                out.extend(data or [])
                break
        return out

    try:
        # Modules and states are small; one GET each.
        modules_raw = _get("/modules/")
        modules = (
            modules_raw.get("results", modules_raw)
            if isinstance(modules_raw, dict) else modules_raw
        ) or []

        states_raw = _get("/states/")
        states = (
            states_raw.get("results", states_raw)
            if isinstance(states_raw, dict) else states_raw
        ) or []

        issues = _paged("/issues/")
    except _RateLimitError:
        raise
    except Exception:
        return None

    return modules, states, issues


# ── Persist helpers ─────────────────────────────────────────────────

def _resolve_module_name(
    module_ids: list[str] | None,
    module_by_id: dict[str, str],
) -> str | None:
    if not module_ids:
        return None
    for mid in module_ids:
        if mid in module_by_id:
            return module_by_id[mid]
    return None


_DELIVERABLE_PREFIXES = ("D-",)
_ADR_PREFIX = "ADR-"
_PHASE_PREFIX = "Phase-"


def _link_kind_for_external_id(ext: str) -> tuple[str, str] | None:
    """Map a Plane external_id to (kind, ref) of the local artifact.

    Returns None for external_ids we don't link from (or empty).
    """
    if not ext:
        return None
    if ext.startswith(_ADR_PREFIX):
        return ("adr", ext)
    if ext.startswith(_DELIVERABLE_PREFIXES):
        return ("deliverable", ext)
    if ext.startswith(_PHASE_PREFIX):
        return ("phase", ext)
    return None


def _issue_body(name: str, ext: str, state_name: str | None,
                module_name: str | None, description: str) -> str:
    parts: list[str] = [name]
    if ext:
        parts.append(ext)
    if state_name:
        parts.append(state_name)
    if module_name:
        parts.append(module_name)
    if description:
        parts.append(description)
    return " ".join(parts)


def _persist(
    conn: sqlite3.Connection,
    modules: list[dict],
    states: list[dict],
    issues: list[dict],
) -> tuple[int, int, int]:
    state_by_id: dict[str, str] = {}
    for s in states:
        sid = s.get("id")
        nm = s.get("name")
        if sid and nm:
            state_by_id[str(sid)] = str(nm)

    module_by_id: dict[str, str] = {}
    modules_written = 0
    for m in modules:
        mid = m.get("id")
        nm = m.get("name")
        if not mid or not nm:
            continue
        module_by_id[str(mid)] = str(nm)
        conn.execute(
            """
            INSERT INTO plane_modules(name, plane_id, external_id, description, source)
            VALUES(?, ?, ?, ?, 'plane')
            ON CONFLICT(name) DO UPDATE SET
                plane_id=excluded.plane_id,
                external_id=excluded.external_id,
                description=excluded.description,
                source='plane'
            """,
            (
                _safe_str(nm),
                _safe_str(mid),
                _safe_str(m.get("external_id")) or None,
                _safe_str(m.get("description")),
            ),
        )
        modules_written += 1

    issues_written = 0
    links_written = 0
    seen_ext_ids: set[str] = set()
    for it in issues:
        ext = _safe_str(it.get("external_id")).strip()
        if not ext:
            continue
        # Plane allows duplicate external_ids in principle; keep the
        # first occurrence (paged order is stable by created_at).
        if ext in seen_ext_ids:
            continue
        seen_ext_ids.add(ext)

        plane_id = _safe_str(it.get("id"))
        name = _safe_str(it.get("name"))
        state_name = state_by_id.get(_safe_str(it.get("state"))) or None
        module_name = _resolve_module_name(it.get("module_ids"), module_by_id)
        description = _safe_str(
            it.get("description_stripped") or it.get("description_html") or ""
        )
        updated_at = _safe_str(it.get("updated_at")) or None

        conn.execute(
            """
            INSERT INTO plane_issues(
                external_id, plane_id, name, state_name, module_name,
                project_id, description, updated_at, source
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'plane')
            ON CONFLICT(external_id) DO UPDATE SET
                plane_id=excluded.plane_id,
                name=excluded.name,
                state_name=excluded.state_name,
                module_name=excluded.module_name,
                project_id=excluded.project_id,
                description=excluded.description,
                updated_at=excluded.updated_at,
                source='plane'
            """,
            (
                ext,
                plane_id,
                name,
                state_name,
                module_name,
                _safe_str(it.get("project")) or None,
                description,
                updated_at,
            ),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('plane_issue', ?, ?, ?)",
            (ext, name or ext, _issue_body(name, ext, state_name, module_name, description)),
        )
        issues_written += 1

        link = _link_kind_for_external_id(ext)
        if link is not None:
            from_kind, from_ref = link
            conn.execute(
                """
                INSERT OR IGNORE INTO entity_links(
                    from_kind, from_ref, to_kind, to_ref, link_type, source
                ) VALUES(?, ?, 'plane_issue', ?, 'tracked_in', 'plane')
                """,
                (from_kind, from_ref, ext),
            )
            links_written += 1

    return issues_written, modules_written, links_written


def ingest(
    conn: sqlite3.Connection,
    *,
    fetcher: Any = None,
) -> PlaneIngestResult:
    """Run a Plane ingest into `conn`.

    Behaviour:
      - missing creds  → skipped (status='unknown')
      - 429 from Plane → error  ('rate-limited'); prior data preserved
                          by the snapshot/restore wrapper in
                          `app.ingest._ingest_plane`
      - fetch error    → error  ('plane unreachable')
      - otherwise      → ok with counts populated.

    `fetcher` is dependency-injectable for tests: it receives a single
    creds dict and returns (modules, states, issues), or raises
    _RateLimitError, or returns None on other errors.
    """
    creds = _read_creds()
    if not creds:
        return PlaneIngestResult(
            ok=False,
            skipped=True,
            skip_reason="no Plane credentials available",
            error="no Plane credentials available",
        )

    fetch = fetcher or _default_fetcher
    try:
        result = fetch(creds)
    except _RateLimitError as exc:
        return PlaneIngestResult(ok=False, error=f"rate-limited: {exc}")
    except Exception as exc:  # defensive: an injected fetcher shouldn't raise
        return PlaneIngestResult(ok=False, error=f"fetch raised: {exc!r}")

    if result is None:
        return PlaneIngestResult(ok=False, error="plane unreachable or auth failed")

    modules, states, issues = result
    try:
        i, m, l = _persist(conn, list(modules), list(states), list(issues))
    except sqlite3.Error as exc:
        return PlaneIngestResult(ok=False, error=f"sqlite error: {exc!r}")

    return PlaneIngestResult(ok=True, plane_issues=i, plane_modules=m, entity_links=l)
