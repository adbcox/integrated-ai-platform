"""tests/conftest.py — Shared pytest fixtures for the integrated-ai-platform test suite.

Import order is safe: heavy deps (torch, transformers) are never imported here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# ── Repo root ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return Path(__file__).parent.parent


# ── Temporary artifacts tree ──────────────────────────────────────────────────


@pytest.fixture
def tmp_artifacts(tmp_path: Path) -> Path:
    """Create a temporary artifacts/ directory tree for test isolation."""
    artifacts = tmp_path / "artifacts"
    for sub in (
        "stage_rag1",
        "stage_rag2",
        "stage_rag3",
        "stage_rag4",
        "stage_rag5",
        "stage_rag6",
        "stage3_manager",
        "stage4_manager",
        "stage5_manager",
        "stage6_manager",
        "stage7_manager",
        "escalations",
        "events",
        "dlq",
    ):
        (artifacts / sub).mkdir(parents=True, exist_ok=True)
    return artifacts


# ── Plane API mock ────────────────────────────────────────────────────────────


@pytest.fixture
def mock_plane_api() -> MagicMock:
    """Mocked PlaneAPI with sensible defaults for unit tests.

    Methods:
        health_check() → True
        list_issues()  → ([], None)
        upsert_issue() → ({"id": "test-uuid"}, True)
    """
    mock = MagicMock(name="PlaneAPI")
    mock.health_check.return_value = True
    mock.list_issues.return_value  = ([], None)
    mock.upsert_issue.return_value = ({"id": "test-uuid"}, True)
    mock.create_issue.return_value = ({"id": "test-uuid"}, None)
    mock.update_issue.return_value = ({"id": "test-uuid"}, None)
    mock.get_issue.return_value    = ({"id": "test-uuid", "name": "Test"}, None)
    return mock


# ── Ollama mock ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ollama(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch urllib.request.urlopen to simulate Ollama responses.

    Endpoints mocked:
        POST /api/generate   → {"response": '{"title": "Test", "category": "API"}'}
        POST /api/embeddings → {"embedding": [0.1] * 768}
    """
    import io
    import urllib.request

    class _FakeResponse:
        def __init__(self, data: bytes):
            self._data = data
            self.status = 200

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    def _fake_urlopen(request, *args, **kwargs):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "/api/generate" in url:
            payload = json.dumps({"response": '{"title": "Test", "category": "API"}'})
        elif "/api/embeddings" in url or "/api/embed" in url:
            payload = json.dumps({"embedding": [0.1] * 768})
        elif "/api/tags" in url:
            payload = json.dumps({"models": [{"name": "qwen2.5-coder:14b"}]})
        else:
            payload = json.dumps({})
        return _FakeResponse(payload.encode())

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    return _fake_urlopen


# ── Plex API mock ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_plex_api() -> MagicMock:
    """Mocked PlexAPI-style object with standard media server responses."""
    mock = MagicMock(name="PlexAPI")

    # /status/sessions
    session = MagicMock()
    session.type = "episode"
    session.title = "Test Episode"
    session.grandparentTitle = "Test Show"
    session.state = "playing"
    mock.sessions.return_value = [session]

    # /library/sections
    section = MagicMock()
    section.key  = "1"
    section.type = "show"
    section.title = "TV Shows"
    mock.library.sections.return_value = [section]

    return mock


# ── Sample roadmap items ──────────────────────────────────────────────────────


@pytest.fixture
def sample_roadmap_items() -> list[dict]:
    """Ten representative roadmap items covering all status and priority values."""
    return [
        {
            "id": "RM-TEST-001",
            "title": "Implement ExecutorFactory abstraction",
            "category": "Core Infrastructure",
            "priority": "Critical",
            "status": "done",
            "loe": "M",
            "strategic_value": 9,
            "dependencies": [],
            "description": "Abstract executor selection between Claude and Aider",
            "assignee": None,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": "RM-TEST-002",
            "title": "Build stage_rag4 entity-aware reranking",
            "category": "RAG Pipeline",
            "priority": "High",
            "status": "done",
            "loe": "S",
            "strategic_value": 8,
            "dependencies": ["RM-TEST-001"],
            "description": "CamelCase entity extraction + definition scoring",
            "assignee": None,
            "created_at": "2026-01-02T00:00:00Z",
        },
        {
            "id": "RM-TEST-003",
            "title": "Add semantic modification generation",
            "category": "RAG Pipeline",
            "priority": "High",
            "status": "in_progress",
            "loe": "L",
            "strategic_value": 7,
            "dependencies": ["RM-TEST-002"],
            "description": "LLM-based code diff generation with fallback",
            "assignee": None,
            "created_at": "2026-01-03T00:00:00Z",
        },
        {
            "id": "RM-TEST-004",
            "title": "Integrate embeddings for semantic search",
            "category": "RAG Pipeline",
            "priority": "Medium",
            "status": "backlog",
            "loe": "XL",
            "strategic_value": 6,
            "dependencies": ["RM-TEST-003"],
            "description": "Vector embeddings + ANN index",
            "assignee": None,
            "created_at": "2026-01-04T00:00:00Z",
        },
        {
            "id": "RM-TEST-005",
            "title": "Bandwidth throttle for off-hours downloads",
            "category": "Media Ops",
            "priority": "Medium",
            "status": "done",
            "loe": "S",
            "strategic_value": 5,
            "dependencies": [],
            "description": "Business-hours detection + rclone bwlimit",
            "assignee": None,
            "created_at": "2026-01-05T00:00:00Z",
        },
        {
            "id": "RM-TEST-006",
            "title": "Dashboard dependency graph view",
            "category": "Developer UX",
            "priority": "Low",
            "status": "in_progress",
            "loe": "M",
            "strategic_value": 5,
            "dependencies": [],
            "description": "D3.js force-directed graph of roadmap deps",
            "assignee": None,
            "created_at": "2026-01-06T00:00:00Z",
        },
        {
            "id": "RM-TEST-007",
            "title": "Training data annotation pipeline",
            "category": "Training",
            "priority": "High",
            "status": "blocked",
            "loe": "L",
            "strategic_value": 8,
            "dependencies": ["RM-TEST-003", "RM-TEST-004"],
            "description": "Blocked on semantic generation quality",
            "assignee": None,
            "created_at": "2026-01-07T00:00:00Z",
        },
        {
            "id": "RM-TEST-008",
            "title": "Homepage portal integration",
            "category": "Infrastructure",
            "priority": "Low",
            "status": "done",
            "loe": "S",
            "strategic_value": 4,
            "dependencies": [],
            "description": "Homepage service links and status widgets",
            "assignee": None,
            "created_at": "2026-01-08T00:00:00Z",
        },
        {
            "id": "RM-TEST-009",
            "title": "Stage 7 full autonomy loop",
            "category": "Core Infrastructure",
            "priority": "Critical",
            "status": "backlog",
            "loe": "XL",
            "strategic_value": 10,
            "dependencies": ["RM-TEST-003", "RM-TEST-007"],
            "description": "Full autonomous agent with learning loops",
            "assignee": None,
            "created_at": "2026-01-09T00:00:00Z",
        },
        {
            "id": "RM-TEST-010",
            "title": "Load test dashboard API",
            "category": "Quality",
            "priority": "Medium",
            "status": "backlog",
            "loe": "S",
            "strategic_value": 3,
            "dependencies": [],
            "description": "Locust load test for p50/p95 baselines",
            "assignee": None,
            "created_at": "2026-01-10T00:00:00Z",
        },
    ]


# ── EventBus singleton reset ──────────────────────────────────────────────────


@pytest.fixture(autouse=False)
def event_bus_reset() -> Generator[None, None, None]:
    """Reset the EventBus singleton before and after each test.

    Guards against state bleed across tests that publish/subscribe to the bus.
    Skips cleanly if framework.event_system is not installed.
    """
    try:
        from framework.event_system import EventBus

        # Shutdown existing singleton (flushes threads)
        instance = EventBus._instance
        if instance is not None:
            try:
                instance.shutdown()
            except Exception:
                pass
        EventBus._instance = None

        yield

        # Tear down after test
        instance = EventBus._instance
        if instance is not None:
            try:
                instance.shutdown()
            except Exception:
                pass
        EventBus._instance = None

    except ImportError:
        yield  # module not present — no-op


# ── MetricsRegistry singleton reset ─────────────────────────────────────────


@pytest.fixture(autouse=False)
def metrics_reset() -> Generator[None, None, None]:
    """Reset the MetricsRegistry singleton between tests.

    Skips cleanly if framework.metrics is not installed.
    """
    try:
        import framework.metrics as _metrics

        # Clear registry if it exposes one
        registry = getattr(_metrics, "_registry", None) or getattr(_metrics, "registry", None)
        if registry is not None:
            # Best effort — try common patterns
            for attr in ("_counters", "_gauges", "_histograms", "_metrics"):
                if hasattr(registry, attr):
                    getattr(registry, attr).clear()

        yield

        # Repeat clear after test
        for attr in ("_counters", "_gauges", "_histograms", "_metrics"):
            if hasattr(registry, attr):
                getattr(registry, attr).clear()

    except (ImportError, AttributeError):
        yield


# ── Pytest configuration ──────────────────────────────────────────────────────


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to suppress PytestUnknownMarkWarning."""
    config.addinivalue_line("markers", "unit: fast unit test — no I/O")
    config.addinivalue_line("markers", "integration: integration test — may hit filesystem")
    config.addinivalue_line("markers", "e2e: end-to-end test — requires running services")
    config.addinivalue_line("markers", "slow: test that takes >2 seconds")
