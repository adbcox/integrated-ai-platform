"""OpenProject ingester — versions + workpackages + tracked_in entity_links.

Read-only mirror of the OpenProject project (ADR-A-006: xindex consumes
OpenProject state but never writes back). Replaces the prior Plane CE
ingester (D-17-04 WP-17-04-05.5, 2026-05-02). We pull versions,
statuses, and workpackages via the HAL JSON v3 API, denormalize
status_id → status_name and version_id → version_name, and emit
`tracked_in` entity_links from local artifacts (ADRs and
deliverables) to their workpackage when its `external_id` matches:

    'ADR-A-NNN'         → from_kind='adr',         from_ref='ADR-A-NNN'
    'D-NN-MM[.x]'       → from_kind='deliverable', from_ref='D-NN-MM[.x]'
    'Phase-NN'          → from_kind='phase',       from_ref='Phase-NN'

Doctrine:
  - NEVER raises. Network errors, missing token, auth failure →
    return ok=False; the orchestrator restores from snapshot.
  - Token comes from /run/secrets/openproject-credentials.env (rendered
    by the vault-agent-xindex sidecar). Never logged.
  - Direct HAL parsing — no dependency on framework.openproject_connector
    (matches the ingester boundary the original Plane ingester held).
    The 'External ID' custom field is discovered via the work-packages
    /form schema; if absent, falls back to the legacy 'Plane RM ID' CF
    populated at WP-17-04-03 import time.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:  # pragma: no cover — runtime dep, optional in unit tests with stub fetcher
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


CREDENTIALS_PATH = Path(
    os.environ.get(
        "XINDEX_OPENPROJECT_CREDENTIALS",
        "/run/secrets/openproject-credentials.env",
    )
)


EXT_ID_FIELD_NAME = "External ID"
LEGACY_RM_FIELD_NAME = "Plane RM ID"


@dataclass
class OpenProjectIngestResult:
    ok: bool
    op_workpackages: int = 0
    op_versions: int = 0
    entity_links: int = 0
    error: str = ""
    skipped: bool = False
    skip_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "op_workpackages": self.op_workpackages,
            "op_versions": self.op_versions,
            "entity_links": self.entity_links,
            "error": self.error,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


def _read_creds() -> dict[str, str] | None:
    """Return {'token','url','project'} or None if any missing.

    Reads OPENPROJECT_API_TOKEN / OPENPROJECT_URL / OPENPROJECT_PROJECT
    from env first, then falls back to the credentials file rendered by
    the vault-agent-xindex sidecar.
    """
    out: dict[str, str] = {}
    env_keys = {
        "OPENPROJECT_API_TOKEN": "token",
        "OPENPROJECT_URL": "url",
        "OPENPROJECT_PROJECT": "project",
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


# ── Default fetcher (direct HAL JSON v3 against OpenProject) ───────────────

def _default_fetcher(
    creds: dict[str, str],
) -> tuple[list[dict], list[dict], list[dict]] | None:
    """Return (versions, statuses, workpackages) or None on failure.

    Talks OpenProject HAL JSON v3 directly via stdlib + requests; mirrors
    the boundary the original Plane ingester held (ADR-A-006: ingester
    independent of framework code).
    """
    if requests is None:
        return None
    base = creds["url"].rstrip("/")
    project_identifier = creds["project"]

    sess = requests.Session()
    sess.auth = ("apikey", creds["token"])
    sess.headers.update({"Accept": "application/json"})

    def _get(path: str, params: dict | None = None) -> Any:
        r = sess.get(f"{base}/api/v3{path}", params=params, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json() if r.content else {}

    def _post(path: str, body: dict) -> Any:
        # POST is used only against /work_packages/form, which is a
        # READ operation in OpenProject's idiom (returns the schema)
        # and never mutates server state.
        r = sess.post(
            f"{base}/api/v3{path}",
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json() if r.content else {}

    try:
        # 1. Resolve project numeric id from identifier.
        proj = _get(f"/projects/{project_identifier}")
        if not proj:
            return None
        project_id = int(proj["id"])

        # 2. Discover custom-field id for 'External ID' (or legacy 'Plane RM ID')
        #    via project work-package form schema.
        ext_cf_id, legacy_cf_id = _discover_external_id_cf(_post, project_id)

        # 3. Statuses (system-wide).
        st_data = _get("/statuses")
        st_elements = (st_data or {}).get("_embedded", {}).get("elements", [])
        statuses = [
            {"id": int(s["id"]), "name": s["name"],
             "is_closed": bool(s.get("isClosed"))}
            for s in st_elements
        ]

        # 4. Versions (project-scoped).
        v_data = _get(f"/projects/{project_id}/versions")
        v_elements = (v_data or {}).get("_embedded", {}).get("elements", [])
        versions = [
            {
                "id": int(v["id"]),
                "name": v["name"],
                "external_id": v["name"],
                "description": (v.get("description") or {}).get("raw", ""),
            }
            for v in v_elements
        ]

        # 5. Work packages (paginated).
        workpackages = _list_workpackages(
            _get, project_id, ext_cf_id, legacy_cf_id
        )
    except Exception:
        return None

    return versions, statuses, workpackages


def _discover_external_id_cf(
    post: Any, project_id: int
) -> tuple[int | None, int | None]:
    """Return (external_id_cf_id, legacy_rm_cf_id) from the WP form schema."""
    try:
        form = post(f"/projects/{project_id}/work_packages/form", {})
    except Exception:
        return None, None
    schema = (form or {}).get("_embedded", {}).get("schema", {})
    ext_id: int | None = None
    legacy_id: int | None = None
    for key, descr in schema.items():
        if not key.startswith("customField"):
            continue
        try:
            cf_id = int(key.replace("customField", ""))
        except ValueError:
            continue
        nm = descr.get("name") if isinstance(descr, dict) else None
        if nm == EXT_ID_FIELD_NAME:
            ext_id = cf_id
        elif nm == LEGACY_RM_FIELD_NAME:
            legacy_id = cf_id
    return ext_id, legacy_id


def _list_workpackages(
    get: Any,
    project_id: int,
    ext_cf_id: int | None,
    legacy_cf_id: int | None,
) -> list[dict]:
    cf_key = f"customField{ext_cf_id}" if ext_cf_id else None
    legacy_key = f"customField{legacy_cf_id}" if legacy_cf_id else None
    out: list[dict] = []
    offset = 1
    page_size = 200
    filters = (
        f'[{{"project":{{"operator":"=","values":["{project_id}"]}}}}]'
    )
    while True:
        data = get(
            "/work_packages",
            {"filters": filters, "pageSize": page_size, "offset": offset},
        )
        if not data:
            break
        elements = data.get("_embedded", {}).get("elements", [])
        for wp in elements:
            ext = ""
            if cf_key:
                ext = wp.get(cf_key) or ""
            if not ext and legacy_key:
                ext = wp.get(legacy_key) or ""
            status_link = wp.get("_links", {}).get("status", {}).get("href", "")
            status_id = status_link.rsplit("/", 1)[-1] if status_link else ""
            version_link = wp.get("_links", {}).get("version", {}).get("href", "") or ""
            version_id = version_link.rsplit("/", 1)[-1] if version_link else ""
            out.append({
                "external_id": ext,
                "name": wp.get("subject", ""),
                "id": int(wp["id"]),
                "state": int(status_id) if status_id.isdigit() else None,
                "version_id": int(version_id) if version_id.isdigit() else None,
                "description_html": (wp.get("description") or {}).get("html", ""),
                "description_raw": (wp.get("description") or {}).get("raw", ""),
                "updated_at": wp.get("updatedAt", "") or "",
                "project_id": project_id,
            })
        total = int(data.get("total", 0) or 0)
        if offset * page_size >= total or not elements:
            break
        offset += 1
    return out


# ── Persist helpers ─────────────────────────────────────────────────

def _resolve_version_name(
    version_id: int | None,
    version_by_id: dict[int, str],
) -> str | None:
    if version_id is None:
        return None
    return version_by_id.get(version_id)


_DELIVERABLE_PREFIXES = ("D-",)
_ADR_PREFIX = "ADR-"
_PHASE_PREFIX = "Phase-"


def _link_kind_for_external_id(ext: str) -> tuple[str, str] | None:
    """Map an OpenProject external_id to (kind, ref) of the local artifact."""
    if not ext:
        return None
    if ext.startswith(_ADR_PREFIX):
        return ("adr", ext)
    if ext.startswith(_DELIVERABLE_PREFIXES):
        return ("deliverable", ext)
    if ext.startswith(_PHASE_PREFIX):
        return ("phase", ext)
    return None


def _wp_body(name: str, ext: str, status_name: str | None,
             version_name: str | None, description: str) -> str:
    parts: list[str] = [name]
    if ext:
        parts.append(ext)
    if status_name:
        parts.append(status_name)
    if version_name:
        parts.append(version_name)
    if description:
        parts.append(description)
    return " ".join(parts)


def _persist(
    conn: sqlite3.Connection,
    versions: list[dict],
    statuses: list[dict],
    workpackages: list[dict],
) -> tuple[int, int, int]:
    status_by_id: dict[int, str] = {}
    for s in statuses:
        sid = s.get("id")
        nm = s.get("name")
        if sid is not None and nm:
            status_by_id[int(sid)] = str(nm)

    version_by_id: dict[int, str] = {}
    versions_written = 0
    for v in versions:
        vid = v.get("id")
        nm = v.get("name")
        if vid is None or not nm:
            continue
        version_by_id[int(vid)] = str(nm)
        conn.execute(
            """
            INSERT INTO op_versions(name, op_id, external_id, description, source)
            VALUES(?, ?, ?, ?, 'openproject')
            ON CONFLICT(name) DO UPDATE SET
                op_id=excluded.op_id,
                external_id=excluded.external_id,
                description=excluded.description,
                source='openproject'
            """,
            (
                _safe_str(nm),
                _safe_str(vid),
                _safe_str(v.get("external_id")) or _safe_str(nm),
                _safe_str(v.get("description")),
            ),
        )
        versions_written += 1

    wps_written = 0
    links_written = 0
    seen_ext_ids: set[str] = set()
    for wp in workpackages:
        ext = _safe_str(wp.get("external_id")).strip()
        if not ext:
            continue
        # Defensive: OpenProject's CF doesn't enforce uniqueness either.
        if ext in seen_ext_ids:
            continue
        seen_ext_ids.add(ext)

        op_id = _safe_str(wp.get("id"))
        name = _safe_str(wp.get("name"))
        status_id = wp.get("state")
        status_name = status_by_id.get(int(status_id)) if isinstance(status_id, int) else None
        version_name = _resolve_version_name(wp.get("version_id"), version_by_id)
        description = _safe_str(
            wp.get("description_raw") or wp.get("description_html") or ""
        )
        updated_at = _safe_str(wp.get("updated_at")) or None

        conn.execute(
            """
            INSERT INTO op_workpackages(
                external_id, op_id, name, status_name, version_name,
                project_id, description, updated_at, source
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'openproject')
            ON CONFLICT(external_id) DO UPDATE SET
                op_id=excluded.op_id,
                name=excluded.name,
                status_name=excluded.status_name,
                version_name=excluded.version_name,
                project_id=excluded.project_id,
                description=excluded.description,
                updated_at=excluded.updated_at,
                source='openproject'
            """,
            (
                ext,
                op_id,
                name,
                status_name,
                version_name,
                _safe_str(wp.get("project_id")) or None,
                description,
                updated_at,
            ),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('workpackage', ?, ?, ?)",
            (ext, name or ext, _wp_body(name, ext, status_name, version_name, description)),
        )
        wps_written += 1

        link = _link_kind_for_external_id(ext)
        if link is not None:
            from_kind, from_ref = link
            conn.execute(
                """
                INSERT OR IGNORE INTO entity_links(
                    from_kind, from_ref, to_kind, to_ref, link_type, source
                ) VALUES(?, ?, 'workpackage', ?, 'tracked_in', 'openproject')
                """,
                (from_kind, from_ref, ext),
            )
            links_written += 1

    return wps_written, versions_written, links_written


def ingest(
    conn: sqlite3.Connection,
    *,
    fetcher: Any = None,
) -> OpenProjectIngestResult:
    """Run an OpenProject ingest into `conn`.

    Behaviour:
      - missing creds  → skipped (status='unknown')
      - fetch error    → error; prior op_workpackages / op_versions /
                          tracked_in entity_links preserved by the
                          snapshot/restore wrapper in
                          `app.ingest._ingest_openproject`
      - otherwise      → ok with counts populated.

    `fetcher` is dependency-injectable for tests: it receives a single
    creds dict and returns (versions, statuses, workpackages), or
    returns None on failure.
    """
    creds = _read_creds()
    if not creds:
        return OpenProjectIngestResult(
            ok=False,
            skipped=True,
            skip_reason="no OpenProject credentials available",
            error="no OpenProject credentials available",
        )

    fetch = fetcher or _default_fetcher
    try:
        result = fetch(creds)
    except Exception as exc:  # defensive: an injected fetcher shouldn't raise
        return OpenProjectIngestResult(ok=False, error=f"fetch raised: {exc!r}")

    if result is None:
        return OpenProjectIngestResult(
            ok=False, error="openproject unreachable or auth failed"
        )

    versions, statuses, workpackages = result
    try:
        w, v, l = _persist(
            conn, list(versions), list(statuses), list(workpackages)
        )
    except sqlite3.Error as exc:
        return OpenProjectIngestResult(ok=False, error=f"sqlite error: {exc!r}")

    return OpenProjectIngestResult(
        ok=True, op_workpackages=w, op_versions=v, entity_links=l
    )
