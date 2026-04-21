"""Seam tests for LACE2-P10-REGIME-COMPARATOR-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.benchmark_regime_comparator import BenchmarkRegimeComparator, RegimeComparisonRecord


def test_import_comparator():
    assert callable(BenchmarkRegimeComparator)


def test_compare_returns_record():
    r = BenchmarkRegimeComparator().compare()
    assert isinstance(r, RegimeComparisonRecord)


def test_lace1_kind_synthetic():
    r = BenchmarkRegimeComparator().compare()
    assert r.lace1_benchmark_kind == "synthetic_baseline"


def test_lace2_kind_real_file():
    r = BenchmarkRegimeComparator().compare()
    assert r.lace2_benchmark_kind == "real_file_baseline"


def test_regime_upgrade_confirmed():
    r = BenchmarkRegimeComparator().compare()
    assert r.regime_upgrade_confirmed is True


def test_emit_artifact(tmp_path):
    cmp = BenchmarkRegimeComparator()
    r = cmp.compare()
    path = cmp.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["lace1_benchmark_kind"] == "synthetic_baseline"
    assert data["lace2_benchmark_kind"] == "real_file_baseline"
    assert data["regime_upgrade_confirmed"] is True
