"""Seam tests for LACE1-P7-REPLAY-RERUN-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.replay_gate import ReplayGate, ReplaySpec
from framework.execution_trace_enricher import EnrichedTrace


def _trace(outcome_class="failure", retry_count=0):
    return EnrichedTrace(trace_id="ETRACE-r1-x", source_result_id="r1",
                         outcome_class=outcome_class, retry_count=retry_count,
                         file_change_count=1, outcome_state="failed", enriched_at="x")


def test_import_gate():
    from framework.replay_gate import ReplayGate
    assert callable(ReplayGate)


def test_failure_is_replayable():
    s = ReplayGate().evaluate(_trace("failure", 0))
    assert s.replayable is True
    assert s.replay_priority == "high"


def test_partial_is_replayable():
    s = ReplayGate().evaluate(_trace("partial", 0))
    assert s.replayable is True


def test_success_not_replayable():
    s = ReplayGate().evaluate(_trace("first_pass_success", 0))
    assert s.replayable is False
    assert s.not_replayable_reason is not None


def test_over_max_retry_not_replayable():
    s = ReplayGate().evaluate(_trace("failure", 3))
    assert s.replayable is False


def test_priority_medium_at_retry_1():
    s = ReplayGate().evaluate(_trace("failure", 1))
    assert s.replay_priority == "medium"
