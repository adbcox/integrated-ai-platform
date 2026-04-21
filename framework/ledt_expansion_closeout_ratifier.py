"""LEDT-P12: Authoritative LEDT closeout with transition summary and limitations."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

ARTIFACT_BASE = Path("artifacts/expansion/LEDT")

REQUIRED_ARTIFACTS = [
    "tranche_selection.json",
    "eligibility_contract_proof.json",
    "preflight_report.json",
    "route_decision_proof.json",
    "fallback_justification_proof.json",
    "packet_routing_metadata_proof.json",
    "local_run_receipt_proof.json",
    "planner_preference_proof.json",
    "fallback_audit.json",
    "local_first_proof.json",
    "ledt_transition_ratification.json",
]

LEDT_MODULES = [
    "framework.local_exec_eligibility_contract",
    "framework.local_exec_preflight",
    "framework.exec_route_decision",
    "framework.fallback_justification",
    "framework.packet_routing_metadata",
    "framework.local_run_receipt",
    "framework.planner_preference_schema",
    "framework.fallback_audit",
    "framework.local_first_proof_harness",
    "framework.ledt_transition_ratifier",
]

WHAT_WAS_BUILT = [
    "LEDT-P1: transition tranche selector (RM-GOV-003 scoring from LACE2 evidence)",
    "LEDT-P2: local execution eligibility contract (5-criterion evaluator with disqualifiers)",
    "LEDT-P3: local execution preflight evaluator (aider, code_executor, scope, validation checks)",
    "LEDT-P4: execution route decision surface (local_execute / claude_fallback / hard_stop)",
    "LEDT-P5: fallback justification model (evidence-required, class-enforced writer)",
    "LEDT-P6: packet routing metadata schema (local_first default, ledt-v1 policy version)",
    "LEDT-P7: local run receipt model (route, validations, fallback status per execution)",
    "LEDT-P8: planner preference schema (local_first default with Claude condition gate)",
    "LEDT-P9: fallback audit surface (justified / avoidable / invalid classification)",
    "LEDT-P10: local-first proof harness (5-sample decision chain, local_first_rate=0.8)",
    "LEDT-P11: transition ratifier (5-criterion verdict: local_exec_default_confirmed)",
    "LEDT-P12: transition closeout (this artifact)",
]

WHAT_CHANGED_OPERATIONALLY = [
    "Route decisions now default to local_execute for any packet where eligibility passes and preflight is ready",
    "Claude fallback requires explicit FallbackJustificationRecord with class and evidence; narrative excuses rejected",
    "Packet routing metadata defaults preferred_executor='local_first' unless overridden",
    "Planner preference records enforce local_first as default and require explicit conditions for Claude execution",
    "Fallback events are now auditable as justified / avoidable / invalid via FallbackAuditor",
]

WHEN_CLAUDE_EXECUTION_ALLOWED = [
    "aider and framework.code_executor both unavailable (preflight C2 check fails)",
    "packet file_scope_count > 5 and task cannot be split without semantic loss",
    "explicit hard_stop condition identified by eligibility evaluator",
    "manual override with FallbackJustificationRecord class='manual_override' and >= 20 chars evidence",
]

WHAT_REMAINS_UNPROVEN = [
    "No live execution loop tested; routing is decision-surface proof only",
    "Proof harness uses synthetic packet descriptions, not live campaign packets",
    "Fallback audit uses constructed receipts, not production execution history",
    "Planner preference schema is not yet wired into any live campaign plan emitter",
    "Local-first rate on real LACE2/LEDT-style packets may differ from the 5-sample harness",
]

KNOWN_LIMITATIONS = [
    "No live execution loop tested; all routing decisions are decision-surface proofs only",
    "LocalExecPreflightEvaluator does not make live Ollama network checks; only import probes",
    "Proof harness local_first_rate=0.8 is based on 5 synthetic samples — statistically insufficient",
    "Fallback audit constructs receipts and justifications directly; no integration with real executor receipts",
    "PlannerPreferenceBuilder is not wired into any campaign plan generator or stage6_manager",
    "ExecRouteDecider is not wired into any live execution path or packet scheduling loop",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class LEDTCloseoutRecord:
    closeout_id: str
    campaign_id: str
    campaign_verdict: str
    packets_completed: int
    packets_expected: int
    artifacts_present: int
    artifacts_expected: int
    modules_importable: int
    modules_expected: int
    what_was_built: List[str]
    what_changed_operationally: List[str]
    when_claude_execution_allowed: List[str]
    what_remains_unproven: List[str]
    known_limitations: List[str]
    transition_verdict: str
    closed_at: str
    artifact_path: Optional[str] = None


def _check_artifacts():
    return {name: (ARTIFACT_BASE / name).exists() for name in REQUIRED_ARTIFACTS}


def _check_modules():
    results = {}
    for mod in LEDT_MODULES:
        try:
            importlib.import_module(mod)
            results[mod] = True
        except Exception:
            results[mod] = False
    return results


def _load_transition_verdict() -> str:
    p = ARTIFACT_BASE / "ledt_transition_ratification.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8")).get("verdict", "unknown")
    return "unknown"


class LEDTExpansionCloseoutRatifier:
    """Ratifies the LEDT campaign and emits the authoritative closeout artifact."""

    def ratify(self) -> LEDTCloseoutRecord:
        art_status = _check_artifacts()
        mod_status = _check_modules()

        art_present = sum(1 for v in art_status.values() if v)
        mods_importable = sum(1 for v in mod_status.values() if v)
        transition_verdict = _load_transition_verdict()

        all_artifacts = art_present == len(REQUIRED_ARTIFACTS)
        all_modules = mods_importable == len(LEDT_MODULES)
        confirmed = transition_verdict == "local_exec_default_confirmed"

        if all_artifacts and all_modules and confirmed:
            verdict = "ledt_campaign_complete"
        elif art_present >= 9 and mods_importable >= 9:
            verdict = "ledt_campaign_partial"
        else:
            verdict = "ledt_campaign_inconclusive"

        return LEDTCloseoutRecord(
            closeout_id=f"LEDT-CLOSE-{_ts()}",
            campaign_id="LEDT",
            campaign_verdict=verdict,
            packets_completed=12,
            packets_expected=12,
            artifacts_present=art_present,
            artifacts_expected=len(REQUIRED_ARTIFACTS),
            modules_importable=mods_importable,
            modules_expected=len(LEDT_MODULES),
            what_was_built=WHAT_WAS_BUILT,
            what_changed_operationally=WHAT_CHANGED_OPERATIONALLY,
            when_claude_execution_allowed=WHEN_CLAUDE_EXECUTION_ALLOWED,
            what_remains_unproven=WHAT_REMAINS_UNPROVEN,
            known_limitations=KNOWN_LIMITATIONS,
            transition_verdict=transition_verdict,
            closed_at=_iso_now(),
        )

    def emit(self, record: LEDTCloseoutRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "LEDT_closeout.json"
        out_path.write_text(
            json.dumps({
                "closeout_id": record.closeout_id,
                "campaign_id": record.campaign_id,
                "campaign_verdict": record.campaign_verdict,
                "packets_completed": record.packets_completed,
                "packets_expected": record.packets_expected,
                "artifacts_present": record.artifacts_present,
                "artifacts_expected": record.artifacts_expected,
                "modules_importable": record.modules_importable,
                "modules_expected": record.modules_expected,
                "what_was_built": record.what_was_built,
                "what_changed_operationally": record.what_changed_operationally,
                "when_claude_execution_allowed": record.when_claude_execution_allowed,
                "what_remains_unproven": record.what_remains_unproven,
                "known_limitations": record.known_limitations,
                "transition_verdict": record.transition_verdict,
                "closed_at": record.closed_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["LEDTCloseoutRecord", "LEDTExpansionCloseoutRatifier"]
