"""Seam tests for LACE1-P11-FAILURE-PATTERN-MINING-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.failure_pattern_miner import FailurePatternMiner, FailurePattern, FailurePatternReport
from framework.lace1_benchmark_runner import Lace1BenchmarkRunner, BenchmarkRunReport


def _report() -> BenchmarkRunReport:
    return Lace1BenchmarkRunner().run()


def test_import_miner():
    from framework.failure_pattern_miner import FailurePatternMiner
    assert callable(FailurePatternMiner)


def test_mine_returns_report():
    r = FailurePatternMiner().mine(_report())
    assert isinstance(r, FailurePatternReport)


def test_zero_benchmark_failures_on_clean_pack():
    r = FailurePatternMiner().mine(_report())
    assert r.benchmark_failures == 0


def test_patterns_list_is_list():
    r = FailurePatternMiner().mine(_report())
    assert isinstance(r.patterns, list)
    assert all(isinstance(p, FailurePattern) for p in r.patterns)


def test_total_patterns_matches_list():
    r = FailurePatternMiner().mine(_report())
    assert r.total_patterns == len(r.patterns)


def test_emit_writes_json(tmp_path):
    miner = FailurePatternMiner()
    r = miner.mine(_report())
    path = miner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "report_id" in data
    assert "benchmark_failures" in data
    assert "patterns" in data
