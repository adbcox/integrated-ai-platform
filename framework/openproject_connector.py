"""OpenProject API v3 connector — replaces framework/plane_connector.py.

D-17-04 WP-17-04-04. The minimal API surface is whatever
scripts/openproject-sync-from-framework.py calls; it intentionally
mirrors the Plane connector's call signatures so the sync script can
be a structural port rather than a rewrite.

Auth: HTTP basic auth with username "apikey" and password = the
iap-sync user's token (from secret/openproject/api#token, provisioned
by scripts/openproject-mint-iap-sync-token.sh).

API surface (HAL JSON, OpenProject v3):
- Statuses, Types, Priorities are system-wide; we look them up by name once.
- Categories and Versions are project-scoped (the natural fit for
  Plane's Labels and Modules respectively).
- WorkPackages carry a custom field "Plane RM ID" which we use as
  external_id during the migration cycle (already populated for the
  670 issues imported by WP-17-04-03). The connector uses Plane RM ID
  for legacy lookups but writes a second custom field "External ID"
  for new (post-Plane) deliverables keyed by D-NN-XX / Phase-NN.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))


class RateLimitError(Exception):
    """OpenProject doesn't rate-limit by default, but the sync's call sites
    catch RateLimitError before the broad `except Exception` (Plane-era
    Discovery #15). Keep the symbol for call-site compatibility — it is
    raised on HTTP 429 if the operator ever turns rate limiting on."""


def _requests():
    import requests
    return requests


# ── Mapping: PROJECT_FRAMEWORK status → OpenProject status name ────────────

MARKDOWN_TO_OP_STATUS: dict[str, str] = {
    "DONE":        "Closed",
    "IN PROGRESS": "In progress",
    "NOT STARTED": "New",
    "DEFERRED":    "On hold",
    # Convenience aliases used elsewhere in the framework
    "Accepted":    "New",
    "Planning":    "New",
    "Planned":     "New",
    "In progress": "In progress",
    "Completed":   "Closed",
    "Retired":     "Rejected",
}

PRIORITY_MAP: dict[str, str] = {
    "Critical": "Immediate",
    "High":     "High",
    "Medium":   "Normal",
    "Low":      "Low",
    "None":     "Normal",
    "urgent":   "Immediate",
    "high":     "High",
    "medium":   "Normal",
    "low":      "Low",
    "none":     "Normal",
}


# ── Simple in-memory cache (mirrors plane_connector._Cache) ────────────────

class _Cache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry[1] < time.time():
                return None
            return entry[0]

    def set(self, key: str, value: Any, ttl: float = 60.0) -> None:
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def invalidate(self, prefix: str = "") -> None:
        with self._lock:
            for k in list(self._store.keys()):
                if k.startswith(prefix):
                    self._store.pop(k, None)


_cache = _Cache()


class OpenProjectAPI:
    """OpenProject REST API v3 client.

    Required env vars (or pass to __init__):
        OPENPROJECT_URL          http://192.168.10.145:8086
        OPENPROJECT_API_TOKEN    iap-sync user's API token
        OPENPROJECT_PROJECT      project identifier (default: "roadmap")

    The 'External ID' custom field is created on first use; the existing
    'Plane RM ID' custom field is preserved (it's still the legacy lookup
    key for issues imported from Plane).
    """

    EXT_ID_FIELD_NAME = "External ID"
    LEGACY_RM_FIELD_NAME = "Plane RM ID"

    def __init__(
        self,
        base_url: str = "",
        api_token: str = "",
        project_identifier: str = "",
    ) -> None:
        self.base_url = (base_url or os.environ.get(
            "OPENPROJECT_URL", "http://192.168.10.145:8086")).rstrip("/")
        self.api_token = api_token or os.environ.get("OPENPROJECT_API_TOKEN", "")
        self.project_identifier = project_identifier or os.environ.get(
            "OPENPROJECT_PROJECT", "roadmap")
        self._session = None
        self._project_id: Optional[int] = None
        self._ext_id_cf_id: Optional[int] = None
        self._legacy_rm_cf_id: Optional[int] = None

    # ── HTTP helpers ───────────────────────────────────────────────────────

    def _sess(self):
        if self._session is None:
            req = _requests()
            s = req.Session()
            s.auth = ("apikey", self.api_token)
            s.headers.update({"Content-Type": "application/json"})
            self._session = s
        return self._session

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v3{path}"

    def _proj_url(self, path: str = "") -> str:
        return self._url(f"/projects/{self._project_id_resolved()}{path}")

    def _request(self, method: str, url: str, **kwargs) -> Any:
        r = self._sess().request(method, url, timeout=15, **kwargs)
        if r.status_code == 429:
            raise RateLimitError(f"429 on {method} {url}")
        if r.status_code in (200, 201):
            return r.json() if r.content else {}
        if r.status_code == 204:
            return {}
        if r.status_code == 404:
            return None
        # Surface OpenProject's structured error
        try:
            err = r.json()
            raise RuntimeError(
                f"{method} {url} → HTTP {r.status_code}: "
                f"{err.get('errorIdentifier','?')} — {err.get('message','?')}"
            )
        except ValueError:
            r.raise_for_status()
        return None

    def _get(self, url: str, params: dict | None = None) -> Any:
        return self._request("GET", url, params=params)

    def _post(self, url: str, data: dict) -> Any:
        return self._request("POST", url, json=data)

    def _patch(self, url: str, data: dict) -> Any:
        return self._request("PATCH", url, json=data)

    def _delete(self, url: str) -> bool:
        return self._request("DELETE", url) is not None or True

    # ── Health ─────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        try:
            me = self._get(self._url("/users/me"))
            return bool(me and me.get("_type") == "User")
        except Exception:
            return False

    # ── Project / custom-field bootstrap ───────────────────────────────────

    def _project_id_resolved(self) -> int:
        if self._project_id is not None:
            return self._project_id
        proj = self._get(self._url(f"/projects/{self.project_identifier}"))
        if not proj:
            raise RuntimeError(
                f"OpenProject project '{self.project_identifier}' not found"
            )
        self._project_id = int(proj["id"])
        return self._project_id

    def _ensure_ext_id_field(self) -> int:
        """Find or create the 'External ID' WP custom field. Cached."""
        if self._ext_id_cf_id is not None:
            return self._ext_id_cf_id
        # /api/v3/custom_fields requires admin; iap-sync isn't admin. We
        # discover via a WP form schema instead, which exposes the
        # custom-field IDs available on this project's default type.
        # Fall back to lazy cache from environment / hardcoded if needed.
        env_id = os.environ.get("OPENPROJECT_EXT_ID_CF_ID")
        if env_id and env_id.isdigit():
            self._ext_id_cf_id = int(env_id)
            return self._ext_id_cf_id
        # Heuristic: query project schema and find a string CF named "External ID".
        schema_url = self._proj_url(f"/work_packages/form")
        # POST an empty form to get the schema (OP idiom)
        try:
            form = self._request("POST", schema_url, json={})
            schema = form.get("_embedded", {}).get("schema", {})
            for key, descr in schema.items():
                if not key.startswith("customField"):
                    continue
                if descr.get("name") == self.EXT_ID_FIELD_NAME:
                    self._ext_id_cf_id = int(key.replace("customField", ""))
                    return self._ext_id_cf_id
                if descr.get("name") == self.LEGACY_RM_FIELD_NAME and self._legacy_rm_cf_id is None:
                    self._legacy_rm_cf_id = int(key.replace("customField", ""))
        except Exception:
            pass
        # If 'External ID' doesn't exist, the iap-sync user can't create
        # WP custom fields (admin only). Operator must run the bootstrap
        # script (openproject-bootstrap-ext-id-field.sh, future) or
        # create it via UI. Until then, fall back to legacy field.
        if self._legacy_rm_cf_id is not None:
            self._ext_id_cf_id = self._legacy_rm_cf_id
            return self._ext_id_cf_id
        raise RuntimeError(
            f"neither '{self.EXT_ID_FIELD_NAME}' nor '{self.LEGACY_RM_FIELD_NAME}' "
            "custom field found on project; admin must create it"
        )

    # ── Statuses (system-wide; cached) ─────────────────────────────────────

    def _list_statuses(self) -> list[dict]:
        cached = _cache.get("statuses")
        if cached is not None:
            return cached
        # Reachable for any authenticated user that has at least one
        # workflow row defined for their role (empty workflows → 403).
        # The mint-iap-sync-token script clones Member's workflows into
        # IAP Sync to satisfy this.
        data = self._get(self._url("/statuses"))
        elements = (data or {}).get("_embedded", {}).get("elements", [])
        statuses = [{"id": int(s["id"]), "name": s["name"], "is_closed": bool(s.get("isClosed"))}
                    for s in elements]
        _cache.set("statuses", statuses, ttl=300)
        return statuses

    def get_status_id(self, status_name: str) -> Optional[int]:
        for s in self._list_statuses():
            if s["name"].lower() == status_name.lower():
                return s["id"]
        return None

    def list_statuses(self) -> list[dict]:
        """Public accessor for system statuses. Read-only consumers (xindex
        ingester) need id→name resolution without depending on the private
        `_list_statuses` symbol."""
        return list(self._list_statuses())

    def ensure_states(self) -> dict[str, int]:
        """Compatibility shim — returns the canonical Plane-era state names
        mapped to the OpenProject status IDs they map onto. Sync code that
        used `states["Done"]` continues to work."""
        statuses = {s["name"]: s["id"] for s in self._list_statuses()}
        out: dict[str, int] = {}
        for plane_name, op_name in [
            ("Backlog",     "New"),
            ("In Progress", "In progress"),
            ("Done",        "Closed"),
            ("Cancelled",   "Rejected"),
            ("On hold",     "On hold"),
        ]:
            if op_name in statuses:
                out[plane_name] = statuses[op_name]
        return out

    # ── Priorities (system-wide; cached) ───────────────────────────────────

    def _list_priorities(self) -> list[dict]:
        cached = _cache.get("priorities")
        if cached is not None:
            return cached
        form = self._request("POST", self._proj_url("/work_packages/form"), json={})
        schema = form.get("_embedded", {}).get("schema", {})
        allowed = schema.get("priority", {}).get("_embedded", {}).get("allowedValues", [])
        prios = [{"id": int(p["id"]), "name": p["name"]} for p in allowed]
        _cache.set("priorities", prios, ttl=300)
        return prios

    def get_priority_id(self, name: str) -> Optional[int]:
        op_name = PRIORITY_MAP.get(name, name)
        for p in self._list_priorities():
            if p["name"].lower() == op_name.lower():
                return p["id"]
        return None

    # ── Default Type (cached) ──────────────────────────────────────────────

    def _default_type_id(self) -> int:
        cached = _cache.get("default_type")
        if cached is not None:
            return cached
        form = self._request("POST", self._proj_url("/work_packages/form"), json={})
        schema = form.get("_embedded", {}).get("schema", {})
        allowed = schema.get("type", {}).get("_embedded", {}).get("allowedValues", [])
        # Prefer "Task"; fall back to first allowed
        for t in allowed:
            if t.get("name") == "Task":
                _cache.set("default_type", int(t["id"]), ttl=300)
                return int(t["id"])
        if allowed:
            tid = int(allowed[0]["id"])
            _cache.set("default_type", tid, ttl=300)
            return tid
        raise RuntimeError("no allowed types on project")

    # ── Categories (project-scoped — Plane Labels analog) ─────────────────

    def list_categories(self, use_cache: bool = True) -> list[dict]:
        key = f"categories:{self._project_id_resolved()}"
        if use_cache:
            cached = _cache.get(key)
            if cached is not None:
                return cached
        data = self._get(self._proj_url("/categories"))
        results = data.get("_embedded", {}).get("elements", []) if data else []
        # Normalize id type
        out = [{"id": int(c["id"]), "name": c["name"]} for c in results]
        _cache.set(key, out, ttl=300)
        return out

    def get_category_id(self, name: str) -> Optional[int]:
        for c in self.list_categories():
            if c["name"].lower() == name.lower():
                return c["id"]
        return None

    def ensure_label(self, name: str) -> int:
        """Plane-era name; here it returns the project-category id."""
        cid = self.get_category_id(name)
        if cid:
            return cid
        # iap-sync has manage_categories per its role definition
        created = self._post(self._proj_url("/categories"), {"name": name[:30]})
        _cache.invalidate(f"categories:{self._project_id_resolved()}")
        return int(created["id"])

    def ensure_labels_bulk(self, names: list[str]) -> dict[str, int]:
        existing = {c["name"].lower(): c["id"] for c in self.list_categories()}
        out: dict[str, int] = {}
        for n in names:
            if n.lower() in existing:
                out[n] = existing[n.lower()]
            else:
                out[n] = self.ensure_label(n)
                existing[n.lower()] = out[n]
        return out

    # ── Versions (Plane Modules analog) ────────────────────────────────────

    def list_modules(self, use_cache: bool = True) -> list[dict]:
        key = f"versions:{self._project_id_resolved()}"
        if use_cache:
            cached = _cache.get(key)
            if cached is not None:
                return cached
        data = self._get(self._proj_url("/versions"))
        results = data.get("_embedded", {}).get("elements", []) if data else []
        # OP versions don't natively support external_id; we encode it
        # as the version name itself (matches the convention from
        # WP-17-04-03 import where modules were imported by name).
        out = [{
            "id": int(v["id"]),
            "name": v["name"],
            "external_id": v["name"],
            "description": (v.get("description") or {}).get("raw", ""),
        } for v in results]
        _cache.set(key, out, ttl=300)
        return out

    def get_module_by_external_id(self, external_id: str) -> Optional[dict]:
        for v in self.list_modules():
            if v["external_id"] == external_id or v["name"] == external_id:
                return v
        return None

    def get_module_by_name(self, name: str) -> Optional[dict]:
        for v in self.list_modules():
            if v["name"].lower() == name.lower():
                return v
        return None

    def create_module(
        self,
        name: str,
        description: str = "",
        external_id: str | None = None,
    ) -> dict:
        # external_id collapses to name for OP versions
        payload = {
            "name": (external_id or name)[:60],
            "description": {"raw": description},
        }
        created = self._post(self._proj_url("/versions"), payload)
        _cache.invalidate(f"versions:{self._project_id_resolved()}")
        return {
            "id": int(created["id"]),
            "name": created["name"],
            "external_id": created["name"],
        }

    def ensure_module(
        self,
        external_id: str,
        name: str,
        description: str = "",
    ) -> tuple[dict, bool]:
        existing = self.get_module_by_external_id(external_id)
        if existing:
            return existing, False
        created = self.create_module(name=name, description=description, external_id=external_id)
        return created, True

    def list_module_issues(self, module_id: int) -> list[int]:
        """Return WP IDs whose version_id equals module_id."""
        data = self._get(
            self._proj_url(f"/work_packages"),
            params={"filters": f'[{{"version":{{"operator":"=","values":["{module_id}"]}}}}]', "pageSize": 500},
        )
        if not data:
            return []
        return [int(wp["id"]) for wp in data.get("_embedded", {}).get("elements", [])]

    def add_issues_to_module(self, module_id: int, issue_ids: list[int]) -> dict:
        """OpenProject doesn't have a bulk module-add endpoint; iterate
        and PATCH each WP's version_id link. Idempotent."""
        if not issue_ids:
            return {}
        for wp_id in issue_ids:
            payload = {
                "_links": {
                    "version": {"href": f"/api/v3/versions/{module_id}"}
                },
                "lockVersion": self._wp_lock_version(wp_id),
            }
            self._patch(self._url(f"/work_packages/{wp_id}"), payload)
        return {"added": len(issue_ids)}

    def _wp_lock_version(self, wp_id: int) -> int:
        wp = self._get(self._url(f"/work_packages/{wp_id}"))
        return int(wp.get("lockVersion", 0))

    # ── Work packages (Plane Issues analog) ────────────────────────────────

    def list_all_issues(self) -> list[dict]:
        """Fetch all WPs in the project with external_id (Plane RM ID or
        new External ID) materialized into a flat key for diff lookup."""
        ext_cf_id = self._ensure_ext_id_field()
        cf_key = f"customField{ext_cf_id}"
        legacy_key = f"customField{self._legacy_rm_cf_id}" if self._legacy_rm_cf_id else None
        out: list[dict] = []
        offset = 1
        page_size = 200
        while True:
            data = self._get(
                self._url(f"/work_packages"),
                params={
                    "filters": f'[{{"project":{{"operator":"=","values":["{self._project_id_resolved()}"]}}}}]',
                    "pageSize": page_size,
                    "offset": offset,
                },
            )
            if not data:
                break
            elements = data.get("_embedded", {}).get("elements", [])
            for wp in elements:
                ext = wp.get(cf_key)
                if not ext and legacy_key:
                    ext = wp.get(legacy_key)
                state_link = wp.get("_links", {}).get("status", {}).get("href", "")
                state_id = state_link.rsplit("/", 1)[-1] if state_link else ""
                version_link = wp.get("_links", {}).get("version", {}).get("href", "") or ""
                version_id = version_link.rsplit("/", 1)[-1] if version_link else ""
                out.append({
                    "id": int(wp["id"]),
                    "external_id": ext or "",
                    "name": wp.get("subject", ""),
                    "description_html": (wp.get("description") or {}).get("html", ""),
                    "description_raw": (wp.get("description") or {}).get("raw", ""),
                    "state": int(state_id) if state_id.isdigit() else None,
                    "version_id": int(version_id) if version_id.isdigit() else None,
                    "updated_at": wp.get("updatedAt", "") or "",
                    "project_id": self._project_id_resolved(),
                    "_lock": int(wp.get("lockVersion", 0)),
                })
            total = data.get("total", 0)
            if offset * page_size >= total:
                break
            offset += 1
        return out

    def get_issue(self, issue_id: int) -> dict:
        return self._get(self._url(f"/work_packages/{issue_id}"))

    def get_issue_by_external_id(self, external_id: str) -> Optional[dict]:
        # Linear scan against the cached full list (cheaper than
        # filter-on-CF on a 670-WP project, which OP doesn't index well)
        for wp in self.list_all_issues():
            if wp.get("external_id") == external_id:
                return wp
        return None

    def create_issue(
        self,
        name: str,
        description: str = "",
        state_id: int | None = None,
        priority: str = "medium",
        label_ids: list[int] | None = None,
        external_id: str | None = None,
        estimate: str | None = None,
    ) -> dict:
        ext_cf_id = self._ensure_ext_id_field()
        payload: dict[str, Any] = {
            "subject": name[:255],
            "description": {"format": "markdown", "raw": _strip_tags(description)},
            "_links": {
                "type": {"href": f"/api/v3/types/{self._default_type_id()}"},
                "project": {"href": f"/api/v3/projects/{self._project_id_resolved()}"},
            },
        }
        if state_id:
            payload["_links"]["status"] = {"href": f"/api/v3/statuses/{state_id}"}
        prio_id = self.get_priority_id(priority)
        if prio_id:
            payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{prio_id}"}
        if label_ids:
            # Use first label as category (OpenProject WP has 1 category, not many)
            payload["_links"]["category"] = {"href": f"/api/v3/categories/{label_ids[0]}"}
        if external_id:
            payload[f"customField{ext_cf_id}"] = external_id
        result = self._post(self._url("/work_packages"), payload)
        return self._materialize_wp(result)

    def update_issue(self, issue_id: int, updates: dict) -> dict:
        """Translate the Plane-shape update dict into OpenProject's HAL form
        and PATCH it. Refetches lockVersion to avoid 409s."""
        ext_cf_id = self._ensure_ext_id_field()
        wp = self._get(self._url(f"/work_packages/{issue_id}"))
        payload: dict[str, Any] = {"lockVersion": int(wp.get("lockVersion", 0))}
        links: dict[str, Any] = {}
        if "name" in updates:
            payload["subject"] = updates["name"][:255]
        if "description_html" in updates:
            payload["description"] = {
                "format": "markdown",
                "raw": _strip_tags(updates["description_html"]),
            }
        if "state" in updates:
            links["status"] = {"href": f"/api/v3/statuses/{updates['state']}"}
        if "priority" in updates:
            pid = self.get_priority_id(updates["priority"])
            if pid:
                links["priority"] = {"href": f"/api/v3/priorities/{pid}"}
        if "labels" in updates and updates["labels"]:
            links["category"] = {"href": f"/api/v3/categories/{updates['labels'][0]}"}
        if "external_id" in updates:
            payload[f"customField{ext_cf_id}"] = updates["external_id"]
        if links:
            payload["_links"] = links
        result = self._patch(self._url(f"/work_packages/{issue_id}"), payload)
        return self._materialize_wp(result)

    def update_issue_state(self, issue_id: int, state_name: str) -> dict:
        sid = self.get_status_id(MARKDOWN_TO_OP_STATUS.get(state_name, state_name))
        if not sid:
            raise ValueError(f"State not found: {state_name!r}")
        return self.update_issue(issue_id, {"state": sid})

    def delete_issue(self, issue_id: int) -> bool:
        return self._delete(self._url(f"/work_packages/{issue_id}"))

    def upsert_issue(
        self,
        external_id: str,
        title: str,
        description: str,
        state_name: str,
        category: str,
        priority: str = "medium",
    ) -> tuple[dict, bool]:
        states = self.ensure_states()
        plane_state = state_name if state_name in states else "Backlog"
        op_state_name = MARKDOWN_TO_OP_STATUS.get(state_name, "New")
        state_id = self.get_status_id(op_state_name)
        category_id = self.ensure_label(category)
        full_name = f"[{external_id}] {title}"

        existing = self.get_issue_by_external_id(external_id)
        if existing:
            updates: dict[str, Any] = {"name": full_name}
            if state_id:
                updates["state"] = state_id
            updates["labels"] = [category_id]
            updates["priority"] = priority
            issue = self.update_issue(existing["id"], updates)
            return issue, False
        else:
            issue = self.create_issue(
                name=full_name,
                description=description,
                state_id=state_id,
                priority=priority,
                label_ids=[category_id],
                external_id=external_id,
            )
            return issue, True

    def get_stats(self) -> dict:
        statuses = {s["id"]: s["name"] for s in self._list_statuses()}
        all_wps = self.list_all_issues()
        counts: dict[str, int] = {}
        for wp in all_wps:
            sname = statuses.get(wp.get("state"), "Unknown")
            counts[sname] = counts.get(sname, 0) + 1
        return {"total": len(all_wps), "by_state": counts}

    def get_stats_fast(self) -> dict:
        data = self._get(
            self._url("/work_packages"),
            params={
                "filters": f'[{{"project":{{"operator":"=","values":["{self._project_id_resolved()}"]}}}}]',
                "pageSize": 1,
            },
        )
        return {"total": data.get("total", 0) if data else 0, "by_state": {}}

    # ── Internal ───────────────────────────────────────────────────────────

    def _materialize_wp(self, wp: dict) -> dict:
        """Reduce a HAL WP envelope to the Plane-shape dict the sync expects."""
        if not wp:
            return {}
        ext_cf_id = self._ensure_ext_id_field()
        cf_key = f"customField{ext_cf_id}"
        state_link = wp.get("_links", {}).get("status", {}).get("href", "")
        state_id = state_link.rsplit("/", 1)[-1] if state_link else ""
        return {
            "id": int(wp["id"]),
            "external_id": wp.get(cf_key, ""),
            "name": wp.get("subject", ""),
            "description_html": (wp.get("description") or {}).get("html", ""),
                    "description_raw": (wp.get("description") or {}).get("raw", ""),
            "state": int(state_id) if state_id.isdigit() else None,
            "_lock": int(wp.get("lockVersion", 0)),
        }


def _strip_tags(html: str) -> str:
    """OpenProject takes markdown-formatted descriptions; strip Plane's HTML
    wrapping to a clean text representation. Sync's HTML envelope is
    already minimal (mostly <p> + <code>), and operators read both
    formats fine."""
    import re
    s = html or ""
    # Normalise Plane's <div> wrapper (added on read; stripped on round-trip)
    s = s.strip()
    if s.startswith("<div>") and s.endswith("</div>"):
        s = s[len("<div>"):-len("</div>")]
    # Convert simple constructs to markdown
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s, flags=re.DOTALL)
    s = re.sub(r"<p>(.*?)</p>", r"\1\n\n", s, flags=re.DOTALL)
    # Strip remaining tags
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()
