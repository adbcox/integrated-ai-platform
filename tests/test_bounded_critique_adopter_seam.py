"""Conformance tests for framework/bounded_critique_adopter.py (LARAC2-CRITIQUE-ADOPTION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.bounded_critique_adopter import BoundedCritiqueAdopter, CritiqueAdoptionRecord


# --- import and type ---

def test_import_bounded_critique_adopter():
    assert callable(BoundedCritiqueAdopter)


def test_returns_critique_adoption_record():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "some error")
    assert isinstance(r, CritiqueAdoptionRecord)


# --- fields ---

def test_result_fields_present():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "err")
    assert hasattr(r, "task_kind")
    assert hasattr(r, "last_error")
    assert hasattr(r, "should_retry")
    assert hasattr(r, "critique_text")
    assert hasattr(r, "extra_guidance")
    assert hasattr(r, "evaluated_at")


# --- memory_store=None works ---

def test_memory_store_none_works():
    r = BoundedCritiqueAdopter(memory_store=None).evaluate("text_replacement", "err")
    assert isinstance(r, CritiqueAdoptionRecord)


# --- should_retry is bool ---

def test_should_retry_is_bool():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "IndentationError")
    assert isinstance(r.should_retry, bool)


# --- task_kind preserved ---

def test_task_kind_preserved():
    r = BoundedCritiqueAdopter().evaluate("helper_insertion", "error")
    assert r.task_kind == "helper_insertion"


# --- last_error preserved ---

def test_last_error_preserved():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "SyntaxError line 5")
    assert r.last_error == "SyntaxError line 5"


# --- last_error None works ---

def test_no_error_works():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", None)
    assert isinstance(r, CritiqueAdoptionRecord)


# --- critique_text is string ---

def test_critique_text_is_string():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "err")
    assert isinstance(r.critique_text, str)


# --- extra_guidance is string ---

def test_extra_guidance_is_string():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "err")
    assert isinstance(r.extra_guidance, str)


# --- evaluated_at is string ---

def test_evaluated_at_is_string():
    r = BoundedCritiqueAdopter().evaluate("text_replacement", "err")
    assert isinstance(r.evaluated_at, str)
    assert len(r.evaluated_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "BoundedCritiqueAdopter")
    assert hasattr(framework, "CritiqueAdoptionRecord")
