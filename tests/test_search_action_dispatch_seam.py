"""Conformance tests for framework/search_action_dispatch.py (ADSC1-SEARCH-DISPATCH-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.search_action_dispatch import dispatch_search
from framework.tool_schema import SearchAction, SearchObservation
from framework.workspace_scope import ToolPathScope


def _make_scope(tmp_path):
    return ToolPathScope(source_root=tmp_path)


# --- import and type ---

def test_import_dispatch_search():
    assert callable(dispatch_search)


def test_returns_search_observation(tmp_path):
    scope = _make_scope(tmp_path)
    result = dispatch_search(SearchAction(query="anything"), scope)
    assert isinstance(result, SearchObservation)


# --- valid query against real repo ---

def test_valid_query_returns_observation(tmp_path):
    scope = ToolPathScope(source_root=REPO_ROOT)
    result = dispatch_search(SearchAction(query="retrieve_context"), scope)
    assert isinstance(result, SearchObservation)
    assert result.error is None


def test_valid_query_matches_are_strings(tmp_path):
    scope = ToolPathScope(source_root=REPO_ROOT)
    result = dispatch_search(SearchAction(query="dispatch_search"), scope)
    for m in result.matches:
        assert isinstance(m, str)


def test_valid_query_nonempty_matches(tmp_path):
    scope = ToolPathScope(source_root=REPO_ROOT)
    result = dispatch_search(SearchAction(query="dispatch apply patch"), scope)
    assert len(result.matches) > 0


# --- empty query ---

def test_empty_query_returns_empty_matches(tmp_path):
    scope = _make_scope(tmp_path)
    result = dispatch_search(SearchAction(query="   "), scope)
    assert result.matches == ()
    assert result.error is None


def test_empty_query_observation_fields(tmp_path):
    scope = _make_scope(tmp_path)
    result = dispatch_search(SearchAction(query=""), scope)
    assert result.query == ""
    assert isinstance(result.matches, tuple)


# --- source_root defaulting ---

def test_source_root_defaults_to_scope(tmp_path):
    scope = ToolPathScope(source_root=REPO_ROOT)
    result = dispatch_search(SearchAction(query="workspace_scope"), scope)
    assert isinstance(result, SearchObservation)


def test_source_root_override(tmp_path):
    scope = _make_scope(tmp_path)
    result = dispatch_search(SearchAction(query="x"), scope, source_root=REPO_ROOT)
    assert isinstance(result, SearchObservation)


# --- error propagation ---

def test_nonexistent_source_root_gives_error_or_empty(tmp_path):
    scope = _make_scope(tmp_path)
    result = dispatch_search(SearchAction(query="something"), scope, source_root=tmp_path / "no_such")
    # may get empty matches or error — must not raise
    assert isinstance(result, SearchObservation)


# --- observation fields ---

def test_query_echoed_in_observation(tmp_path):
    scope = ToolPathScope(source_root=REPO_ROOT)
    result = dispatch_search(SearchAction(query="tool_schema"), scope)
    assert result.query == "tool_schema"


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "dispatch_search")
    assert callable(framework.dispatch_search)
