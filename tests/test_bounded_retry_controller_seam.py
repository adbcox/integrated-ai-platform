"""Conformance tests for framework/bounded_retry_controller.py (LARAC2-RETRY-GUIDANCE-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.bounded_retry_controller import BoundedRetryController, RetryDecisionRecord


# --- import and type ---

def test_import_bounded_retry_controller():
    assert callable(BoundedRetryController)


def test_returns_retry_decision_record():
    r = BoundedRetryController().decide("s", 0, "text_replacement", "err")
    assert isinstance(r, RetryDecisionRecord)


# --- fields ---

def test_result_fields_present():
    r = BoundedRetryController().decide("s", 0, "text_replacement", "err")
    assert hasattr(r, "session_id")
    assert hasattr(r, "attempt_number")
    assert hasattr(r, "max_retries")
    assert hasattr(r, "task_kind")
    assert hasattr(r, "last_error")
    assert hasattr(r, "decision")
    assert hasattr(r, "rationale")
    assert hasattr(r, "evaluated_at")


# --- max_retries enforcement ---

def test_stop_at_max_retries():
    ctrl = BoundedRetryController(max_retries=3)
    r = ctrl.decide("s", 3, "text_replacement", "err")
    assert r.decision == "stop"
    assert "max_retries" in r.rationale


def test_stop_above_max_retries():
    ctrl = BoundedRetryController(max_retries=2)
    r = ctrl.decide("s", 5, "text_replacement", "err")
    assert r.decision == "stop"


def test_allow_below_max_retries():
    ctrl = BoundedRetryController(max_retries=5)
    r = ctrl.decide("s", 0, "text_replacement", "IndentationError")
    assert r.decision in {"retry", "stop"}  # critique determines; must not raise


# --- session_id and task_kind preserved ---

def test_session_id_preserved():
    r = BoundedRetryController().decide("my-session", 0, "text_replacement", "err")
    assert r.session_id == "my-session"


def test_task_kind_preserved():
    r = BoundedRetryController().decide("s", 0, "helper_insertion", "err")
    assert r.task_kind == "helper_insertion"


# --- no error works ---

def test_no_error_works():
    r = BoundedRetryController().decide("s", 0, "text_replacement", None)
    assert isinstance(r, RetryDecisionRecord)


# --- decision is valid string ---

def test_decision_valid():
    r = BoundedRetryController().decide("s", 0, "text_replacement", "err")
    assert r.decision in {"retry", "stop"}


# --- max_retries default ---

def test_default_max_retries():
    ctrl = BoundedRetryController()
    assert ctrl._max_retries == 3


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "BoundedRetryController")
    assert hasattr(framework, "RetryDecisionRecord")
