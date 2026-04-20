"""Developer assistance service layer — Phase 1.

Pure-Python service. No external deps beyond stdlib and pathlib.
Not exported from framework/__init__ to avoid side effects;
callers import directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
RUNTIME_DIR: Path = REPO_ROOT / "runtime"
MANIFEST_PATH: Path = RUNTIME_DIR / "developer_assistance_manifest.json"
TOOL_REGISTRY_PATH: Path = RUNTIME_DIR / "developer_assistance_tool_registry.json"
REVIEW_QUEUE_PATH: Path = RUNTIME_DIR / "developer_assistance_review_queue.json"
SESSIONS_PATH: Path = RUNTIME_DIR / "developer_assistance_sessions.json"


def load_manifest() -> dict[str, Any]:
    """Load and return the manifest; raises FileNotFoundError if absent."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_tool_registry() -> dict[str, Any]:
    """Load and return the tool registry; raises FileNotFoundError if absent."""
    if not TOOL_REGISTRY_PATH.exists():
        raise FileNotFoundError(f"tool registry not found: {TOOL_REGISTRY_PATH}")
    return json.loads(TOOL_REGISTRY_PATH.read_text(encoding="utf-8"))


def get_status() -> dict[str, Any]:
    """Return a summary status dict for operator inspection. Never raises."""
    manifest: dict[str, Any] = {}
    manifest_present = False
    try:
        manifest = load_manifest()
        manifest_present = True
    except FileNotFoundError:
        pass

    registry: dict[str, Any] = {}
    tool_registry_present = False
    try:
        registry = load_tool_registry()
        tool_registry_present = True
    except FileNotFoundError:
        pass

    tool_count = len(registry.get("tools", [])) if tool_registry_present else 0

    open_review_count = 0
    if REVIEW_QUEUE_PATH.exists():
        try:
            items = json.loads(REVIEW_QUEUE_PATH.read_text(encoding="utf-8"))
            if isinstance(items, list):
                open_review_count = sum(
                    1 for item in items
                    if isinstance(item, dict) and item.get("status") != "resolved"
                )
        except Exception:  # noqa: BLE001
            pass

    session_count = 0
    if SESSIONS_PATH.exists():
        try:
            sessions = json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
            if isinstance(sessions, list):
                session_count = len(sessions)
        except Exception:  # noqa: BLE001
            pass

    return {
        "subsystem": manifest.get("subsystem", "developer_assistance"),
        "phase": manifest.get("phase", 1),
        "status": manifest.get("status", "unknown"),
        "model_id": manifest.get("model_id", "unknown"),
        "ollama_endpoint": manifest.get("ollama_endpoint", "unknown"),
        "tool_count": tool_count,
        "open_review_count": open_review_count,
        "session_count": session_count,
        "manifest_present": manifest_present,
        "tool_registry_present": tool_registry_present,
    }


def list_tools(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    """Return the list of tool entries from the registry.

    Optionally filtered to enabled tools only.
    """
    registry = load_tool_registry()
    tools: list[dict[str, Any]] = registry.get("tools", [])
    if enabled_only:
        tools = [t for t in tools if t.get("enabled", False)]
    return tools


__all__ = [
    "MANIFEST_PATH",
    "TOOL_REGISTRY_PATH",
    "load_manifest",
    "load_tool_registry",
    "get_status",
    "list_tools",
]
