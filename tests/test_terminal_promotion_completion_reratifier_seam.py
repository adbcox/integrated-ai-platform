"""Seam tests for TerminalPromotionReratifier (TERMINAL-PROMOTION-COMPLETION-RERATIFIER-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.terminal_promotion_reratifier import (
    TerminalPromotionDecision,
    TerminalPromotionReratifier,
    emit_terminal_promotion_decision,
)


def _aider_done():
    return {"decision": "aider_done", "blocking_reason": None}


def _aider_partial(reason="wired_checker_called=false"):
    return {"decision": "aider_partial", "blocking_reason": reason}


def test_import_terminal_reratifier():
    assert callable(TerminalPromotionReratifier)


def test_aider_done_with_full_count_yields_complete():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_done(),
        prior_resolved_count=7,
        total_count=8,
    )
    assert d.terminal_decision == "terminal_promotion_complete"


def test_aider_done_increments_resolved_count():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_done(),
        prior_resolved_count=7,
        total_count=8,
    )
    assert d.resolved_count == 8


def test_aider_partial_yields_terminal_partial():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_partial(),
        prior_resolved_count=7,
        total_count=8,
    )
    assert d.terminal_decision == "terminal_promotion_partial"


def test_aider_partial_preserves_prior_resolved_count():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_partial(),
        prior_resolved_count=7,
        total_count=8,
    )
    assert d.resolved_count == 7


def test_aider_partial_unresolved_items_populated():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_partial("some blocker"),
        prior_resolved_count=7,
        total_count=8,
    )
    assert len(d.unresolved_items) >= 1
    assert "aider_overall" in d.unresolved_items[0]


def test_aider_done_unresolved_items_empty():
    d = TerminalPromotionReratifier().decide(
        aider_promotion_decision=_aider_done(),
        prior_resolved_count=7,
        total_count=8,
    )
    assert d.unresolved_items == []


def test_returns_terminal_promotion_decision():
    d = TerminalPromotionReratifier().decide(aider_promotion_decision=_aider_done())
    assert isinstance(d, TerminalPromotionDecision)


def test_artifact_written(tmp_path):
    d = TerminalPromotionReratifier().decide(aider_promotion_decision=_aider_done())
    path = emit_terminal_promotion_decision(d, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    d = TerminalPromotionReratifier().decide(aider_promotion_decision=_aider_done())
    path = emit_terminal_promotion_decision(d, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "terminal_decision" in data
    assert "aider_decision" in data
    assert data["terminal_decision"] in ("terminal_promotion_complete", "terminal_promotion_partial")


def test_artifact_path_set(tmp_path):
    d = TerminalPromotionReratifier().decide(aider_promotion_decision=_aider_done())
    path = emit_terminal_promotion_decision(d, artifact_dir=tmp_path)
    assert d.artifact_path == path


def test_package_surface():
    import framework
    assert hasattr(framework, "TerminalPromotionReratifier")
    assert hasattr(framework, "TerminalPromotionDecision")
    assert hasattr(framework, "emit_terminal_promotion_decision")
