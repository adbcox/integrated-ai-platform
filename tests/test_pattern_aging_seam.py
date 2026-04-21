"""Conformance tests for framework/pattern_aging.py (ADSC1-PATTERN-AGING-SEAM-1)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.pattern_aging import PatternEvictionResult, evict_stale_patterns, persist_eviction
from framework.repo_pattern_store import PatternEntry, RepoPatternLibrary


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _now():
    return datetime.now(timezone.utc)


def _entry(*, age_days=0, reuse_count=2, suffix=".py"):
    dt = _now() - timedelta(days=age_days)
    return PatternEntry(
        task_kind="text_replacement",
        target_file_suffix=suffix,
        old_string_prefix="old",
        new_string_prefix="new",
        reuse_count=reuse_count,
        recorded_at=_iso(dt),
    )


def _lib(*entries):
    return RepoPatternLibrary(entries=list(entries), total_patterns=len(entries))


# --- import and type ---

def test_import_evict_stale_patterns():
    assert callable(evict_stale_patterns)


def test_returns_tuple():
    lib, res = evict_stale_patterns(_lib())
    assert isinstance(lib, RepoPatternLibrary)
    assert isinstance(res, PatternEvictionResult)


# --- freshness ---

def test_fresh_entry_not_evicted():
    e = _entry(age_days=1, reuse_count=2)
    _, res = evict_stale_patterns(_lib(e), max_age_days=30, min_reuse_count=1)
    assert res.evicted_by_age == 0
    assert res.total_after == 1


# --- age eviction ---

def test_old_entry_evicted_by_age():
    old = _entry(age_days=60, reuse_count=5)
    new = _entry(age_days=1, reuse_count=5)
    _, res = evict_stale_patterns(_lib(old, new), max_age_days=30)
    assert res.evicted_by_age == 1
    assert res.total_after == 1


# --- reuse eviction ---

def test_low_reuse_entry_evicted():
    low = _entry(age_days=1, reuse_count=0)
    high = _entry(age_days=1, reuse_count=3)
    _, res = evict_stale_patterns(_lib(low, high), min_reuse_count=1)
    assert res.evicted_by_reuse == 1
    assert res.total_after == 1


# --- both thresholds combined ---

def test_both_thresholds_applied():
    old_low = _entry(age_days=60, reuse_count=0)
    new_high = _entry(age_days=1, reuse_count=5)
    _, res = evict_stale_patterns(_lib(old_low, new_high))
    assert res.total_after == 1


# --- empty library ---

def test_empty_library_zero_evictions():
    _, res = evict_stale_patterns(_lib())
    assert res.total_before == 0
    assert res.evicted_by_age == 0
    assert res.evicted_by_reuse == 0
    assert res.total_after == 0


# --- accounting ---

def test_total_before_equals_inputs():
    entries = [_entry() for _ in range(4)]
    _, res = evict_stale_patterns(_lib(*entries))
    assert res.total_before == 4


def test_total_after_correct():
    entries = [_entry(age_days=60) for _ in range(3)] + [_entry(age_days=1)]
    _, res = evict_stale_patterns(_lib(*entries), max_age_days=30)
    assert res.total_after == 1


# --- immutability ---

def test_input_library_not_mutated():
    e1 = _entry(age_days=60)
    e2 = _entry(age_days=1)
    lib = _lib(e1, e2)
    original_count = len(lib.entries)
    evict_stale_patterns(lib, max_age_days=30)
    assert len(lib.entries) == original_count


# --- persist ---

def test_persist_writes_parseable_json(tmp_path):
    lib = _lib(_entry())
    new_lib, _ = evict_stale_patterns(lib)
    path = persist_eviction(new_lib, tmp_path)
    data = json.loads(Path(path).read_text())
    assert "entries" in data


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "evict_stale_patterns")
    assert hasattr(framework, "PatternEvictionResult")
    assert hasattr(framework, "persist_eviction")
