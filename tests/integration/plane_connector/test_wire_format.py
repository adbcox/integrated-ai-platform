"""Wire-format regression tests for framework/plane_connector.py.

These tests assert the exact JSON keys sent on the wire to Plane V1.
The bug fixed in 1eed06c (Block 4.C C6 #14, Discovery #16) was that
the connector sent ``label_ids`` instead of ``labels`` — Plane returned
200 OK and silently dropped the field. Plain unit tests would not have
caught it because the connector's Python kwarg is *also* called
``label_ids``; only an inspection of the actual HTTP body would have
surfaced the mismatch.

These tests intercept the ``requests`` layer with a fake session and
assert the payload key by name. They are fast (no real Plane needed)
and run as part of the standard test pack.

Run: pytest tests/integration/plane_connector/
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI, RateLimitError


# ── Fake response / session ──────────────────────────────────────────────────


class _FakeResponse:
    def __init__(self, status_code: int = 200, body: Any = None) -> None:
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.content = json.dumps(self._body).encode() if body is not None else b""

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400 and self.status_code != 429:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeSession:
    """Captures all .request() calls and returns scripted responses."""

    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.calls: list[dict] = []
        self._scripted: dict[tuple[str, str], _FakeResponse] = {}
        self._default = _FakeResponse(200, {})

    def script(self, method: str, url_suffix: str, response: _FakeResponse) -> None:
        """Register a scripted response keyed by method + url-suffix-match."""
        self._scripted[(method.upper(), url_suffix)] = response

    def request(self, method: str, url: str, timeout: int = 15, **kwargs) -> _FakeResponse:
        self.calls.append({
            "method": method.upper(),
            "url":    url,
            "json":   kwargs.get("json"),
            "params": kwargs.get("params"),
        })
        for (m, suffix), resp in self._scripted.items():
            if method.upper() == m and url.endswith(suffix) or suffix in url:
                return resp
        return self._default

    def delete(self, url: str, timeout: int = 15) -> _FakeResponse:
        return self.request("DELETE", url, timeout=timeout)


@pytest.fixture
def fake_api() -> tuple[PlaneAPI, _FakeSession]:
    """Build a PlaneAPI with a fake HTTP session pre-injected."""
    api = PlaneAPI(
        base_url   = "http://plane.test",
        api_token  = "fake-token",
        workspace  = "ws",
        project_id = "proj-uuid",
    )
    sess = _FakeSession()
    api._session = sess  # bypass _sess() lazy init
    return api, sess


# ── F1: create_issue must send "labels" not "label_ids" ──────────────────────


def test_create_issue_sends_labels_key_not_label_ids(fake_api):
    """Discovery #16 regression: payload must use the wire key "labels"."""
    api, sess = fake_api
    sess.script("POST", "/issues/", _FakeResponse(200, {"id": "issue-1", "labels": ["lbl-a"]}))

    api.create_issue(
        name        = "[RM-TEST-1] Test",
        description = "x",
        state_id    = "state-1",
        priority    = "medium",
        label_ids   = ["lbl-a"],
        external_id = "RM-TEST-1",
    )

    posts = [c for c in sess.calls if c["method"] == "POST" and "/issues/" in c["url"]]
    assert posts, "expected a POST to /issues/"
    payload = posts[0]["json"]
    assert "labels" in payload, (
        f"create_issue must send 'labels' key (Plane V1 wire format). "
        f"Payload keys: {list(payload.keys())}"
    )
    assert "label_ids" not in payload, (
        "create_issue must NOT send 'label_ids' (Plane V1 silently drops it). "
        "This was the Block 4.C C6 #14 bug."
    )
    assert payload["labels"] == ["lbl-a"]


def test_create_issue_omits_labels_when_none_provided(fake_api):
    """No labels kwarg → payload should not contain a labels key at all."""
    api, sess = fake_api
    sess.script("POST", "/issues/", _FakeResponse(200, {"id": "issue-2"}))

    api.create_issue(name="[RM-TEST-2] Test", description="x")

    posts = [c for c in sess.calls if c["method"] == "POST"]
    payload = posts[0]["json"]
    assert "labels" not in payload
    assert "label_ids" not in payload


# ── F2: upsert_issue update path must send "labels" not "label_ids" ──────────


def test_upsert_issue_update_path_sends_labels_key(fake_api):
    """Discovery #16 regression on the PATCH path (sibling of F1).

    Until 2026-04-29 the update path silently dropped label changes on
    every existing issue. This test asserts the wire-format fix.
    """
    api, sess = fake_api

    # Prime ensure_states() and ensure_label() to avoid extra round-trips
    states_resp = _FakeResponse(200, {"results": [
        {"id": "state-backlog", "name": "Backlog",   "group": "backlog"},
        {"id": "state-prog",    "name": "In Progress", "group": "started"},
        {"id": "state-done",    "name": "Done",      "group": "completed"},
        {"id": "state-cancel",  "name": "Cancelled", "group": "cancelled"},
    ]})
    labels_resp = _FakeResponse(200, {"results": [{"id": "lbl-api", "name": "API"}]})
    # An "existing" issue lookup
    search_resp = _FakeResponse(200, {"results": [
        {"id": "issue-existing", "name": "[RM-API-100] old"},
    ]})
    patch_resp  = _FakeResponse(200, {"id": "issue-existing"})

    sess.script("GET",   "/states/",  states_resp)
    sess.script("GET",   "/labels/",  labels_resp)
    sess.script("GET",   "/issues/",  search_resp)  # used by get_issue_by_external_id
    sess.script("PATCH", "/issues/issue-existing/", patch_resp)

    api.upsert_issue(
        external_id = "RM-API-100",
        title       = "Updated title",
        description = "x",
        state_name  = "In progress",
        category    = "API",
        priority    = "Medium",
    )

    patches = [c for c in sess.calls if c["method"] == "PATCH"]
    assert patches, "expected a PATCH to update the existing issue"
    payload = patches[0]["json"]
    assert "labels" in payload, (
        f"upsert_issue update path must send 'labels' key. "
        f"Payload keys: {list(payload.keys())}"
    )
    assert "label_ids" not in payload, (
        "upsert_issue must NOT send 'label_ids' on the update path "
        "(Discovery #16 sibling — label updates silently dropped before fix)."
    )
    assert payload["labels"] == ["lbl-api"]


# ── 429 is raised as RateLimitError, not swallowed ───────────────────────────


def test_429_raises_rate_limit_error(fake_api):
    """Discovery #15: 429 must surface as RateLimitError, not generic HTTPError."""
    api, sess = fake_api
    sess.script("GET", "/issues/", _FakeResponse(429, {"detail": "throttled"}))

    with pytest.raises(RateLimitError):
        api.list_issues()


# ── F4: verify_issue_field helper ────────────────────────────────────────────


def test_verify_issue_field_passes_when_value_matches(fake_api):
    api, sess = fake_api
    sess.script("GET", "/issues/issue-x/", _FakeResponse(200, {
        "id": "issue-x", "name": "n", "labels": ["lbl-a"],
    }))
    assert api.verify_issue_field("issue-x", "labels", ["lbl-a"]) is True


def test_verify_issue_field_lists_compared_order_insensitively(fake_api):
    api, sess = fake_api
    sess.script("GET", "/issues/issue-x/", _FakeResponse(200, {
        "id": "issue-x", "labels": ["b", "a", "c"],
    }))
    assert api.verify_issue_field("issue-x", "labels", ["c", "a", "b"]) is True


def test_verify_issue_field_fails_on_mismatch(fake_api):
    api, sess = fake_api
    sess.script("GET", "/issues/issue-x/", _FakeResponse(200, {
        "id": "issue-x", "labels": [],
    }))
    # This is the Discovery #16 worst-case: PATCH returned 200 but the
    # field didn't actually land. verify_issue_field catches it.
    assert api.verify_issue_field("issue-x", "labels", ["lbl-a"]) is False


def test_verify_issue_field_scalar_compare(fake_api):
    api, sess = fake_api
    sess.script("GET", "/issues/issue-x/", _FakeResponse(200, {
        "id": "issue-x", "priority": "high",
    }))
    assert api.verify_issue_field("issue-x", "priority", "high") is True
    assert api.verify_issue_field("issue-x", "priority", "low")  is False


# ── Discovery #14 pagination terminator (regression for connector internals) ─


def test_list_issues_terminates_on_next_page_results_false(fake_api):
    """Plane V1 returns next_cursor=non-null past the end; terminate on
    next_page_results=False or count==0."""
    api, sess = fake_api
    sess.script("GET", "/issues/", _FakeResponse(200, {
        "results": [],
        "count": 0,
        "next_cursor": "10:0:0",
        "next_page_results": False,
    }))

    issues, next_cur = api.list_issues()
    assert issues == []
    assert next_cur is None, "must terminate when next_page_results=False"
