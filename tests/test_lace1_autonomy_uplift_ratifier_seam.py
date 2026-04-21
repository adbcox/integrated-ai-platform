"""Seam tests for LACE1-P12-AUTONOMY-UPLIFT-RATIFIER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.autonomy_uplift_ratifier import (
    AutonomyUpliftRatifier,
    UpliftRatificationRecord,
    VERDICT_SUBSTRATE_UPLIFT_CONFIRMED,
    VERDICT_PARTIAL_SUBSTRATE_UPLIFT,
    VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED,
)
from framework.lace1_benchmark_runner import Lace1BenchmarkRunner
from framework.failure_pattern_miner import FailurePatternMiner


def _bench():
    return Lace1BenchmarkRunner().run()


def _fp(bench):
    return FailurePatternMiner().mine(bench)


def test_import_ratifier():
    from framework.autonomy_uplift_ratifier import AutonomyUpliftRatifier
    assert callable(AutonomyUpliftRatifier)


def test_ratify_returns_record():
    bench = _bench()
    r = AutonomyUpliftRatifier().ratify(bench, _fp(bench))
    assert isinstance(r, UpliftRatificationRecord)


def test_verdict_is_valid():
    bench = _bench()
    r = AutonomyUpliftRatifier().ratify(bench, _fp(bench))
    assert r.verdict in {
        VERDICT_SUBSTRATE_UPLIFT_CONFIRMED,
        VERDICT_PARTIAL_SUBSTRATE_UPLIFT,
        VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED,
    }


def test_benchmark_limitations_present():
    bench = _bench()
    r = AutonomyUpliftRatifier().ratify(bench, _fp(bench))
    assert "benchmark_limitations" in r.__dataclass_fields__
    assert len(r.benchmark_limitations) >= 3


def test_no_real_uplift_claimed():
    bench = _bench()
    r = AutonomyUpliftRatifier().ratify(bench, _fp(bench))
    combined = " ".join(r.benchmark_limitations).lower()
    assert "synthetic" in combined or "not real" in combined or "no real" in combined or "not" in combined


def test_emit_writes_json_with_limitations(tmp_path):
    bench = _bench()
    ratifier = AutonomyUpliftRatifier()
    r = ratifier.ratify(bench, _fp(bench))
    path = ratifier.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "verdict" in data
    assert "benchmark_limitations" in data
    assert len(data["benchmark_limitations"]) >= 3
