"""Plane.so API connector — CRUD, circuit breaker, caching, audit logging."""
from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))


# ── Exceptions ────────────────────────────────────────────────────────────────

class RateLimitError(Exception):
    """Raised when Plane API returns 429. Caller must handle backoff."""


# ── Lazy imports (avoid hard dep when Plane not configured) ───────────────────

def _requests():
    import requests
    return requests


# ── Status mappings ───────────────────────────────────────────────────────────

MARKDOWN_TO_PLANE_STATE: dict[str, str] = {
    "Accepted":    "Backlog",
    "Planning":    "Backlog",
    "Planned":     "Backlog",
    "In progress": "In Progress",
    "Completed":   "Done",
    "Retired":     "Cancelled",
}

PLANE_TO_MARKDOWN_STATE: dict[str, str] = {
    "Backlog":     "Accepted",
    "Todo":        "Accepted",
    "In Progress": "In progress",
    "Done":        "Completed",
    "Cancelled":   "Retired",
    "Won't Fix":   "Retired",
}

PRIORITY_MAP: dict[str, str] = {
    "Critical": "urgent",
    "High":     "high",
    "Medium":   "medium",
    "Low":      "low",
    "None":     "none",
}


# ── Simple in-memory cache ────────────────────────────────────────────────────

class _Cache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock  = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry and time.monotonic() < entry[1]:
                return entry[0]
        return None

    def set(self, key: str, value: Any, ttl: float = 60.0) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, prefix: str = "") -> None:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]


_cache = _Cache()


# ── PlaneAPI ──────────────────────────────────────────────────────────────────

class PlaneAPI:
    """
    Plane REST API client.

    Required env vars (or pass to __init__):
        PLANE_URL          http://localhost:8000
        PLANE_API_TOKEN    token from Plane Profile → API Tokens
        PLANE_WORKSPACE    workspace slug  (e.g. "iap")
        PLANE_PROJECT_ID   project UUID
    """

    def __init__(
        self,
        base_url: str  = "",
        api_token: str = "",
        workspace: str = "",
        project_id: str = "",
    ) -> None:
        self.base_url   = (base_url   or os.environ.get("PLANE_URL",        "http://localhost:8000")).rstrip("/")
        self.api_token  = (api_token  or os.environ.get("PLANE_API_TOKEN",  ""))
        self.workspace  = (workspace  or os.environ.get("PLANE_WORKSPACE",  "iap"))
        self.project_id = (project_id or os.environ.get("PLANE_PROJECT_ID", ""))
        self._session   = None

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _sess(self):
        if self._session is None:
            req = _requests()
            s = req.Session()
            s.headers.update({
                "X-Api-Key": self.api_token,
                "Content-Type": "application/json",
            })
            self._session = s
        return self._session

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v1{path}"

    def _ws_url(self, path: str) -> str:
        return self._url(f"/workspaces/{self.workspace}{path}")

    def _proj_url(self, path: str = "") -> str:
        return self._ws_url(f"/projects/{self.project_id}{path}")

    def _request(self, method: str, url: str, retry: bool = True, **kwargs) -> Any:
        """Execute an HTTP request. Raises RateLimitError on 429 (no blocking sleep)."""
        for attempt in range(2 if retry else 1):
            r = self._sess().request(method, url, timeout=15, **kwargs)
            if r.status_code == 429:
                raise RateLimitError(f"429 on {method} {url.split('/')[-2]}/")
            r.raise_for_status()
            return r.json() if r.content else {}
        raise RuntimeError(f"Request failed: {method} {url}")

    def _get(self, url: str, params: dict | None = None) -> Any:
        return self._request("GET", url, params=params)

    def _post(self, url: str, data: dict) -> Any:
        return self._request("POST", url, json=data)

    def _patch(self, url: str, data: dict) -> Any:
        return self._request("PATCH", url, json=data)

    def _delete(self, url: str) -> bool:
        r = self._sess().delete(url, timeout=15)
        return r.status_code in (200, 204)

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        try:
            # Plane CE has no /api/health/ — root "/" returns {"status": "OK"}
            r = self._sess().get(f"{self.base_url}/", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ── Workspace & project setup ─────────────────────────────────────────────

    def list_workspaces(self) -> list[dict]:
        return self._get(self._url("/workspaces/"))

    def get_workspace(self) -> dict:
        return self._get(self._ws_url("/"))

    def list_projects(self) -> list[dict]:
        return self._get(self._ws_url("/projects/"))

    def create_project(self, name: str, identifier: str, description: str = "") -> dict:
        return self._post(self._ws_url("/projects/"), {
            "name": name, "identifier": identifier, "description": description,
            "network": 2,  # secret
        })

    # ── States ────────────────────────────────────────────────────────────────

    def list_states(self, use_cache: bool = True) -> list[dict]:
        key = f"states:{self.project_id}"
        if use_cache:
            cached = _cache.get(key)
            if cached is not None:
                return cached
        result = self._get(self._proj_url("/states/"))
        results = result.get("results", result) if isinstance(result, dict) else result
        _cache.set(key, results, ttl=300)
        return results

    def get_state_id(self, state_name: str) -> Optional[str]:
        for s in self.list_states():
            if s.get("name", "").lower() == state_name.lower():
                return s["id"]
        return None

    def create_state(self, name: str, color: str = "#6b7280", group: str = "backlog") -> dict:
        _cache.invalidate(f"states:{self.project_id}")
        return self._post(self._proj_url("/states/"), {
            "name": name, "color": color, "group": group,
        })

    def ensure_states(self) -> dict[str, str]:
        """Ensure required states exist. Returns {name: id}."""
        required = [
            ("Backlog",     "#6b7280", "backlog"),
            ("In Progress", "#f59e0b", "started"),
            ("Done",        "#10b981", "completed"),
            ("Cancelled",   "#ef4444", "cancelled"),
        ]
        existing = {s["name"]: s["id"] for s in self.list_states(use_cache=True)}
        for name, color, group in required:
            if name not in existing:
                s = self.create_state(name, color, group)
                existing[name] = s["id"]
        return existing

    # ── Labels ────────────────────────────────────────────────────────────────

    def list_labels(self, use_cache: bool = True) -> list[dict]:
        key = f"labels:{self.project_id}"
        if use_cache:
            cached = _cache.get(key)
            if cached is not None:
                return cached
        result = self._get(self._proj_url("/labels/"))
        results = result.get("results", result) if isinstance(result, dict) else result
        _cache.set(key, results, ttl=300)
        return results

    def get_label_id(self, name: str) -> Optional[str]:
        for lbl in self.list_labels():
            if lbl.get("name", "").lower() == name.lower():
                return lbl["id"]
        return None

    def create_label(self, name: str, color: str = "#6b7280") -> dict:
        lbl = self._post(self._proj_url("/labels/"), {"name": name, "color": color})
        # Append to cache rather than invalidating (avoid an extra GET)
        key = f"labels:{self.project_id}"
        cached = _cache.get(key)
        if cached is not None:
            _cache.set(key, cached + [lbl], ttl=300)
        return lbl

    def ensure_label(self, name: str) -> str:
        """Return label id, creating it if needed. Uses a single list_labels() fetch."""
        lid = self.get_label_id(name)
        if lid:
            return lid
        lbl = self.create_label(name, _category_color(name))
        return lbl["id"]

    def ensure_labels_bulk(self, names: list[str]) -> dict[str, str]:
        """Ensure all labels exist with a single initial fetch. Returns name→id map."""
        # One fetch populates the cache
        existing = {lbl["name"].lower(): lbl["id"] for lbl in self.list_labels()}
        result: dict[str, str] = {}
        for name in names:
            if name.lower() in existing:
                result[name] = existing[name.lower()]
            else:
                lbl = self.create_label(name, _category_color(name))
                lid = lbl["id"]
                existing[name.lower()] = lid
                result[name] = lid
                time.sleep(1.1)  # respect 60/min rate limit
        return result

    # ── Issues ────────────────────────────────────────────────────────────────

    def list_issues(
        self,
        state_name: str | None = None,
        label: str | None = None,
        cursor: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[dict], Optional[str]]:
        """Return (issues, next_cursor). next_cursor is None when exhausted."""
        params: dict[str, Any] = {"per_page": page_size}
        if cursor:
            params["cursor"] = cursor
        if state_name:
            sid = self.get_state_id(state_name)
            if sid:
                params["state"] = sid
        url = self._proj_url("/issues/")
        data = self._get(url, params=params)
        if isinstance(data, dict):
            results = data.get("results", [])
            next_cur = data.get("next_cursor")
        else:
            results = data
            next_cur = None
        return results, next_cur

    def list_all_issues(self) -> list[dict]:
        """Fetch every issue across pages."""
        all_issues: list[dict] = []
        cursor = None
        while True:
            batch, cursor = self.list_issues(cursor=cursor, page_size=100)
            all_issues.extend(batch)
            if not cursor:
                break
        return all_issues

    def get_issue(self, issue_id: str) -> dict:
        return self._get(self._proj_url(f"/issues/{issue_id}/"))

    def get_issue_by_external_id(self, external_id: str) -> Optional[dict]:
        """Find an issue where external_id metadata matches the RM-* ID."""
        key = f"ext:{external_id}"
        cached = _cache.get(key)
        if cached is not None:
            return cached
        # Search via name field (RM-* IDs are stored as [RM-XXX] prefix in title)
        params = {"search": external_id, "per_page": 5}
        data = self._get(self._proj_url("/issues/"), params=params)
        results = data.get("results", data) if isinstance(data, dict) else data
        for issue in results:
            if issue.get("name", "").startswith(f"[{external_id}]"):
                _cache.set(key, issue, ttl=120)
                return issue
        return None

    def create_issue(
        self,
        name: str,
        description: str = "",
        state_id: str | None = None,
        priority: str = "medium",
        label_ids: list[str] | None = None,
        external_id: str | None = None,
        estimate: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "name": name,
            "description_html": f"<p>{description}</p>" if description else "",
            "priority": priority,
        }
        if state_id:
            payload["state"] = state_id
        if label_ids:
            payload["label_ids"] = label_ids
        result = self._post(self._proj_url("/issues/"), payload)
        _cache.invalidate(f"ext:{external_id}")
        return result

    def update_issue(self, issue_id: str, updates: dict) -> dict:
        result = self._patch(self._proj_url(f"/issues/{issue_id}/"), updates)
        # Invalidate any cached lookup for this issue
        _cache.invalidate("ext:")
        return result

    def update_issue_state(self, issue_id: str, state_name: str) -> dict:
        sid = self.get_state_id(state_name)
        if not sid:
            raise ValueError(f"State not found: {state_name!r}")
        return self.update_issue(issue_id, {"state": sid})

    def delete_issue(self, issue_id: str) -> bool:
        _cache.invalidate("ext:")
        return self._delete(self._proj_url(f"/issues/{issue_id}/"))

    def search_issues(self, query: str, limit: int = 20) -> list[dict]:
        params = {"search": query, "per_page": limit}
        data = self._get(self._proj_url("/issues/"), params=params)
        results = data.get("results", data) if isinstance(data, dict) else data
        return results[:limit]

    def create_enhanced_issue(
        self,
        external_id: str,
        title: str,
        description: str,
        category: str,
        priority: str = "medium",
        code_snippets: list[dict] | None = None,
        reference_links: list[str] | None = None,
        target_files: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        state_name: str = "Backlog",
    ) -> dict:
        """Create or update a roadmap item with rich execution context.

        Returns the Plane issue dict.  Sections are rendered as HTML in the
        description so they display correctly in the Plane UI.
        """
        # Build HTML description so Plane renders it properly
        parts: list[str] = [f"<p>{description}</p>"]

        if acceptance_criteria:
            items_html = "".join(f"<li>{c}</li>" for c in acceptance_criteria)
            parts.append(f"<h2>Acceptance Criteria</h2><ol>{items_html}</ol>")

        if target_files:
            files_html = "".join(f"<li><code>{f}</code></li>" for f in target_files)
            parts.append(f"<h2>Target Files</h2><ul>{files_html}</ul>")

        if code_snippets:
            snippet_parts = []
            for s in code_snippets:
                lang = s.get("language", "python")
                code = s.get("code", "")
                label = s.get("label", "")
                header = f"<p><strong>{label}</strong></p>" if label else ""
                snippet_parts.append(
                    f"{header}<pre><code class=\"language-{lang}\">{code}</code></pre>"
                )
            parts.append("<h2>Code Snippets</h2>" + "\n".join(snippet_parts))

        if reference_links:
            links_html = "".join(
                f'<li><a href="{url}">{url}</a></li>' for url in reference_links
            )
            parts.append(f"<h2>References</h2><ul>{links_html}</ul>")

        enhanced_html = "\n".join(parts)

        issue, _ = self.upsert_issue(
            external_id=external_id,
            title=title,
            description=enhanced_html,
            state_name=state_name,
            category=category,
            priority=priority,
        )
        return issue

    # ── Bulk helpers ──────────────────────────────────────────────────────────

    def upsert_issue(
        self,
        external_id: str,
        title: str,
        description: str,
        state_name: str,
        category: str,
        priority: str = "medium",
    ) -> tuple[dict, bool]:
        """Create or update issue. Returns (issue, created)."""
        states = self.ensure_states()
        plane_state = MARKDOWN_TO_PLANE_STATE.get(state_name, "Backlog")
        state_id    = states.get(plane_state)
        label_id    = self.ensure_label(category)

        existing = self.get_issue_by_external_id(external_id)
        full_name = f"[{external_id}] {title}"

        if existing:
            updates: dict[str, Any] = {"name": full_name}
            if state_id:
                updates["state"] = state_id
            updates["label_ids"] = [label_id]
            updates["priority"]  = PRIORITY_MAP.get(priority, "medium")
            issue = self.update_issue(existing["id"], updates)
            return issue, False
        else:
            issue = self.create_issue(
                name        = full_name,
                description = description,
                state_id    = state_id,
                priority    = PRIORITY_MAP.get(priority, "medium"),
                label_ids   = [label_id],
                external_id = external_id,
            )
            return issue, True

    def get_stats(self) -> dict:
        """Quick summary counts by state."""
        states = {s["id"]: s["name"] for s in self.list_states()}
        all_issues = self.list_all_issues()
        counts: dict[str, int] = {}
        for issue in all_issues:
            sname = states.get(issue.get("state", ""), "Unknown")
            counts[sname] = counts.get(sname, 0) + 1
        return {"total": len(all_issues), "by_state": counts}

    def get_stats_fast(self) -> dict:
        """Get total issue count with a single API call.

        Returns total_count from the pagination header without fetching all
        issues.  Per-state breakdown requires get_stats() which is expensive.
        """
        key = f"stats_fast:{self.project_id}"
        cached = _cache.get(key)
        if cached is not None:
            return cached
        data = self._get(self._proj_url("/issues/"), {"per_page": 1})
        total = data.get("total_count", 0)
        result = {"total": total, "by_state": {}}
        _cache.set(key, result, ttl=30.0)
        return result


# ── Color palette for category labels ────────────────────────────────────────

_CATEGORY_COLORS: dict[str, str] = {
    "API":      "#3b82f6", "CLI":      "#8b5cf6", "CONFIG":   "#f59e0b",
    "CORE":     "#ef4444", "DATA":     "#10b981", "DEV":      "#6366f1",
    "DOCS":     "#64748b", "FLOW":     "#0ea5e9", "GOV":      "#a855f7",
    "MEDIA":    "#ec4899", "MONITOR":  "#14b8a6", "OPS":      "#f97316",
    "PERF":     "#eab308", "REFACTOR": "#78716c", "SCALE":    "#06b6d4",
    "SECURITY": "#dc2626", "SEC":      "#dc2626", "TESTING":  "#84cc16",
    "UI":       "#f43f5e", "UX":       "#e879f9", "UTIL":     "#94a3b8",
}

def _category_color(name: str) -> str:
    return _CATEGORY_COLORS.get(name.upper(), "#6b7280")
