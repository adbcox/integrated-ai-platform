"""Seam tests for LACE1-P15-EXPANSION-CLOSEOUT-RATIFIER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_expansion_closeout_ratifier import (
    Lace1ExpansionCloseoutRatifier,
    Lace1CloseoutRecord,
    CAMPAIGN_VERDICT_COMPLETE,
    CAMPAIGN_VERDICT_PARTIAL,
)
from framework.lace1_benchmark_runner import Lace1BenchmarkRunner
from framework.failure_pattern_miner import FailurePatternMiner
from framework.autonomy_uplift_ratifier import AutonomyUpliftRatifier
from framework.grouped_package_expansion_selector import GroupedPackageExpansionSelector


def _uplift():
    bench = Lace1BenchmarkRunner().run()
    fp = FailurePatternMiner().mine(bench)
    return AutonomyUpliftRatifier().ratify(bench, fp)


def _selection():
    return GroupedPackageExpansionSelector().select()


def test_import_ratifier():
    from framework.lace1_expansion_closeout_ratifier import Lace1ExpansionCloseoutRatifier
    assert callable(Lace1ExpansionCloseoutRatifier)


def test_ratify_returns_record():
    r = Lace1ExpansionCloseoutRatifier().ratify(_uplift(), _selection(), packets_completed=15)
    assert isinstance(r, Lace1CloseoutRecord)


def test_campaign_verdict_is_valid():
    r = Lace1ExpansionCloseoutRatifier().ratify(_uplift(), _selection(), packets_completed=15)
    assert r.campaign_verdict in {CAMPAIGN_VERDICT_COMPLETE, CAMPAIGN_VERDICT_PARTIAL}


def test_known_limitations_at_least_3():
    r = Lace1ExpansionCloseoutRatifier().ratify(_uplift(), _selection())
    assert len(r.known_limitations) >= 3


def test_synthetic_caveat_in_limitations():
    r = Lace1ExpansionCloseoutRatifier().ratify(_uplift(), _selection())
    combined = " ".join(r.known_limitations).lower()
    assert "synthetic" in combined


def test_emit_writes_lace1_closeout_json(tmp_path):
    ratifier = Lace1ExpansionCloseoutRatifier()
    r = ratifier.ratify(_uplift(), _selection(), packets_completed=15)
    path = ratifier.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["campaign_id"] == "LACE1"
    assert "campaign_verdict" in data
    assert len(data["known_limitations"]) >= 3
    assert "packets_completed" in data
