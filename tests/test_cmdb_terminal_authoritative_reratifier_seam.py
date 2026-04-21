"""Seam tests for CMDB terminal authoritative reratifier (CMDB-TERMINAL-AUTHORITATIVE-RERATIFIER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_terminal_authoritative_reratifier import (
    CmdbTerminalDecision,
    CmdbTerminalAuthoritativeReratifier,
    emit_cmdb_terminal_decision,
)


def _done():
    return {"decision": "cmdb_done"}


def _deferred(reason="proof failed"):
    return {"decision": "cmdb_deferred", "blocking_reasons": [reason]}


def _prior(td="terminal_promotion_complete"):
    return {"terminal_decision": td}


def test_import_terminal_reratifier():
    assert callable(CmdbTerminalAuthoritativeReratifier)


def test_cmdb_done_updates_matrix_when_prior_deferred():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior(),
        prior_cmdb_row_status="cmdb_deferred",
    )
    assert d.terminal_decision == "terminal_matrix_updated"


def test_cmdb_deferred_leaves_matrix_unchanged():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_deferred(),
        prior_terminal_decision=_prior(),
        prior_cmdb_row_status="cmdb_deferred",
    )
    assert d.terminal_decision == "terminal_matrix_unchanged"


def test_cmdb_done_unchanged_when_prior_already_done():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior(),
        prior_cmdb_row_status="cmdb_done",
    )
    assert d.terminal_decision == "terminal_matrix_unchanged"


def test_cmdb_row_status_propagated():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior(),
    )
    assert d.cmdb_row_status == "cmdb_done"


def test_matrix_impact_is_string():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior(),
    )
    assert isinstance(d.matrix_impact, str)
    assert len(d.matrix_impact) > 0


def test_prior_terminal_decision_propagated():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior("terminal_promotion_complete"),
    )
    assert d.prior_terminal_decision == "terminal_promotion_complete"


def test_returns_cmdb_terminal_decision():
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(),
        prior_terminal_decision=_prior(),
    )
    assert isinstance(d, CmdbTerminalDecision)


def test_decision_from_actual_artifacts():
    cp = json.loads(Path("artifacts/cmdb_authoritative_adoption/cmdb_authoritative_promotion_decision.json").read_text())
    prior_path = Path("artifacts/terminal_promotion_reratification/terminal_promotion_decision.json")
    pt = json.loads(prior_path.read_text()) if prior_path.exists() else {"terminal_decision": "terminal_promotion_complete"}
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=cp, prior_terminal_decision=pt
    )
    assert d.terminal_decision in ("terminal_matrix_updated", "terminal_matrix_unchanged")


def test_emit_artifact_written(tmp_path):
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(), prior_terminal_decision=_prior()
    )
    path = emit_cmdb_terminal_decision(d, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(), prior_terminal_decision=_prior()
    )
    path = emit_cmdb_terminal_decision(d, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "terminal_decision" in data
    assert "cmdb_row_status" in data
    assert "matrix_impact" in data


def test_emit_artifact_path_set(tmp_path):
    d = CmdbTerminalAuthoritativeReratifier().reratify(
        cmdb_promotion_decision=_done(), prior_terminal_decision=_prior()
    )
    path = emit_cmdb_terminal_decision(d, artifact_dir=tmp_path)
    assert d.artifact_path == path


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbTerminalAuthoritativeReratifier")
    assert hasattr(framework, "CmdbTerminalDecision")
