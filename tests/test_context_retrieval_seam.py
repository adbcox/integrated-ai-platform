"""Conformance tests for framework/context_retrieval.py (RMCC1-RETRIEVAL-CONTEXT-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.context_retrieval import (
    RetrievalQuery,
    RetrievedFile,
    RetrievalResult,
    retrieve_context,
    retrieve_file_content,
)
from framework.codebase_repomap import RepomapGenerator


# --- Inspection gate ---

def test_inspection_gate_repomap():
    assert callable(RepomapGenerator)
    assert hasattr(RepomapGenerator, "scan_repository")


# --- Retrieval types ---

def test_retrieval_query_construction():
    q = RetrievalQuery(query="TypedPermissionGate", top_k=3)
    assert q.query == "TypedPermissionGate"
    assert q.top_k == 3


def test_retrieval_result_construction():
    r = RetrievalResult(query="test")
    assert r.query == "test"
    assert r.files == []


# --- Live retrieval ---

def test_live_retrieval_returns_at_least_one_file_for_known_symbol():
    q = RetrievalQuery(query="TypedPermissionGate", top_k=5)
    result = retrieve_context(q, REPO_ROOT)
    assert isinstance(result, RetrievalResult)
    assert len(result.files) >= 1


def test_top_k_respected():
    q = RetrievalQuery(query="dispatch", top_k=2)
    result = retrieve_context(q, REPO_ROOT)
    assert len(result.files) <= 2


def test_results_have_positive_score():
    q = RetrievalQuery(query="TypedPermissionGate evaluate", top_k=5)
    result = retrieve_context(q, REPO_ROOT)
    for f in result.files:
        assert f.score > 0


def test_snippet_non_empty_when_files_found():
    q = RetrievalQuery(query="TypedPermissionGate", top_k=3, include_snippets=True)
    result = retrieve_context(q, REPO_ROOT)
    if result.files:
        assert result.snippet != ""


def test_retrieved_file_has_path_and_score():
    q = RetrievalQuery(query="ToolPermission", top_k=3)
    result = retrieve_context(q, REPO_ROOT)
    for f in result.files:
        assert isinstance(f, RetrievedFile)
        assert f.path
        assert f.score > 0


# --- retrieve_file_content ---

def test_retrieve_file_content_returns_content_on_real_file():
    content = retrieve_file_content("framework/tool_schema.py", REPO_ROOT)
    assert len(content) > 0
    assert "ToolAction" in content


def test_retrieve_file_content_returns_empty_on_nonexistent():
    content = retrieve_file_content("nonexistent/file.py", REPO_ROOT)
    assert content == ""


# --- Determinism and scope ---

def test_unrelated_query_returns_empty_or_low_results():
    q = RetrievalQuery(query="xyzzyabcdefnotexistingsymbol", top_k=5)
    result = retrieve_context(q, REPO_ROOT)
    assert len(result.files) == 0


def test_no_subprocess_in_context_retrieval():
    import framework.context_retrieval as mod
    src = Path(mod.__file__).read_text()
    assert "subprocess" not in src
    assert "socket" not in src


def test_retrieval_package_surface_export():
    import framework
    assert hasattr(framework, "RetrievalQuery")
    assert hasattr(framework, "RetrievalResult")
    assert hasattr(framework, "retrieve_context")
    assert hasattr(framework, "retrieve_file_content")
