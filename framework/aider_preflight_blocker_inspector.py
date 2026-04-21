"""APCC1-P1: Inspect preflight blocker injection paths and emit PreflightBlockerArtifact."""
from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

BLOCKER_PERMISSION_GATE = "permission_gate_active"
BLOCKER_CONFIG_KEYS = "config_keys_present"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PreflightBlockerRecord:
    blocker_name: str
    passing: bool
    observed_detail: str
    injection_path: str
    required_interface: str

    def to_dict(self) -> dict:
        return {
            "blocker_name": self.blocker_name,
            "passing": self.passing,
            "observed_detail": self.observed_detail,
            "injection_path": self.injection_path,
            "required_interface": self.required_interface,
        }


@dataclass
class PreflightBlockerArtifact:
    blocker_records: list
    total_blockers: int
    injectable_blockers: int
    non_injectable_blockers: int
    preflight_checker_constructor: str
    runtime_adapter_constructor: str
    permission_gate_interface: str
    config_surface_interface: str
    generated_at: str
    artifact_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "blocker_records": [r.to_dict() for r in self.blocker_records],
            "total_blockers": self.total_blockers,
            "injectable_blockers": self.injectable_blockers,
            "non_injectable_blockers": self.non_injectable_blockers,
            "preflight_checker_constructor": self.preflight_checker_constructor,
            "runtime_adapter_constructor": self.runtime_adapter_constructor,
            "permission_gate_interface": self.permission_gate_interface,
            "config_surface_interface": self.config_surface_interface,
            "generated_at": self.generated_at,
            "artifact_path": self.artifact_path,
        }


def inspect_preflight_blockers(
    *,
    artifact_dir: Path = Path("artifacts/preflight_blocker_inspector"),
    dry_run: bool = True,
) -> PreflightBlockerArtifact:
    from framework.aider_preflight import AiderPreflightChecker as _APC
    from framework.aider_runtime_adapter import AiderRuntimeAdapter as _ARA
    from framework.typed_permission_gate import TypedPermissionGate as _TPG, ToolPermission as _TP

    apc_sig = str(inspect.signature(_APC.__init__))
    ara_sig = str(inspect.signature(_ARA.__init__))
    tpg_sig = str(inspect.signature(_TPG.__init__))
    tp_repr = repr(list(_TP))

    # Config surface: AiderPreflightChecker accepts config as plain dict,
    # checking required_keys {"model", "edit_format"} against dict.keys()
    config_surface = "dict with keys: model, edit_format"

    # Determine injection paths
    # permission_gate_active: injectable via `gate=` kwarg of AiderPreflightChecker
    gate_injectable = "gate" in apc_sig
    gate_injection_path = (
        "AiderPreflightChecker(gate=<TypedPermissionGate>)" if gate_injectable
        else "NO_INJECTABLE_PATH"
    )

    # config_keys_present: injectable via `config=` kwarg of AiderPreflightChecker (plain dict)
    config_injectable = "config" in apc_sig
    config_injection_path = (
        "AiderPreflightChecker(config={'model': ..., 'edit_format': ...})" if config_injectable
        else "NO_INJECTABLE_PATH"
    )

    records = [
        PreflightBlockerRecord(
            blocker_name=BLOCKER_PERMISSION_GATE,
            passing=False,
            observed_detail="AiderPreflightChecker instantiated with no gate= kwarg; check fails",
            injection_path=gate_injection_path,
            required_interface=f"TypedPermissionGate instance; constructor sig: {tpg_sig}",
        ),
        PreflightBlockerRecord(
            blocker_name=BLOCKER_CONFIG_KEYS,
            passing=False,
            observed_detail="AiderPreflightChecker instantiated with no config= kwarg; missing keys: model, edit_format",
            injection_path=config_injection_path,
            required_interface=config_surface,
        ),
    ]

    injectable = sum(1 for r in records if r.injection_path != "NO_INJECTABLE_PATH")
    non_injectable = len(records) - injectable

    if non_injectable > 0:
        non_inj_names = [r.blocker_name for r in records if r.injection_path == "NO_INJECTABLE_PATH"]
        raise RuntimeError(
            f"HARD STOP: non_injectable_blockers={non_injectable}; "
            f"blockers with no injectable path: {non_inj_names}"
        )

    artifact = PreflightBlockerArtifact(
        blocker_records=records,
        total_blockers=len(records),
        injectable_blockers=injectable,
        non_injectable_blockers=non_injectable,
        preflight_checker_constructor=apc_sig,
        runtime_adapter_constructor=ara_sig,
        permission_gate_interface=tpg_sig,
        config_surface_interface=config_surface,
        generated_at=_iso_now(),
    )

    if not dry_run:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "blocker_inspector.json"
        out_path.write_text(json.dumps(artifact.to_dict(), indent=2))
        artifact.artifact_path = str(out_path)

    return artifact
