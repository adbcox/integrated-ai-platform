#!/usr/bin/env python3
"""
run_provenance_backfill.py — D-17-122 WP-05 backfill runner.

Reads config/model_provenance/ollama_to_hf_mapping.yaml, runs provenancekit scan
for each scannable model (skipping cloud_only, derivatives, gated-without-token),
persists JSON records to artifacts/model_provenance/.

Usage:
    python3 bin/run_provenance_backfill.py [--dry-run] [--model <ollama_name>]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
MAPPING_FILE = REPO_ROOT / "config" / "model_provenance" / "ollama_to_hf_mapping.yaml"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "model_provenance"
VENV_PROVENANCEKIT = REPO_ROOT / "venv-provenance" / "bin" / "provenancekit"
KIT_VERSION = "1.0.0"

SKIP_DERIVATION_TYPES = {"local_modelfile_derivative", "cloud_only"}


def safe_model_filename(ollama_name: str) -> str:
    return ollama_name.replace(":", "_").replace("/", "_")


def run_scan(hf_id: str, timeout: int = 300) -> tuple[int, str]:
    """Run provenancekit scan, return (returncode, stdout+stderr)."""
    cmd = [str(VENV_PROVENANCEKIT), "scan", hf_id, "--json", "--top-k", "3"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    combined = result.stdout + result.stderr
    return result.returncode, combined


def extract_top_match(scan_stdout: str) -> dict:
    """Parse provenancekit JSON output, return top match dict or empty.

    The kit emits spinner/ANSI on stderr and JSON on stdout, but warning lines
    about unauthenticated HF requests may appear after the JSON object on stdout.
    Use raw_decode() to parse exactly one JSON object from the first '{'.
    """
    idx = scan_stdout.find('{')
    if idx == -1:
        return {}
    decoder = json.JSONDecoder()
    try:
        d, _ = decoder.raw_decode(scan_stdout, idx)
        if isinstance(d, dict):
            return d
    except json.JSONDecodeError:
        pass
    return {}


def build_record(entry: dict, scan_data: dict, hf_id_used: str,
                 verdict: str, confidence: float | None,
                 reason: str, caveats: list[str]) -> dict:
    top_match = (scan_data.get("matches") or [{}])[0]
    scores = top_match.get("scores", {})
    return {
        "model_id": entry["ollama_name"],
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "upstream_hf_id": hf_id_used,
        "upstream_hf_id_from_mapping": entry.get("upstream_hf_id"),
        "derivation_type": entry.get("derivation_type", "unknown"),
        "cisco_kit_version": KIT_VERSION,
        "verdict": verdict,
        "confidence": confidence,
        "reason": reason,
        "provenance_decision": top_match.get("provenance_decision"),
        "pipeline_score": scores.get("pipeline_score"),
        "mfi_score": scores.get("mfi_score"),
        "tokenizer_score": scores.get("tokenizer_score"),
        "match_count": scan_data.get("match_count", 0),
        "elapsed_ms": scan_data.get("elapsed_ms"),
        "base_model_provenance_ref": entry.get("base_model", None),
        "hf_id_confidence": entry.get("hf_id_confidence", "unknown"),
        "scope_caveats": caveats,
    }


def scan_model(entry: dict, dry_run: bool) -> dict:
    ollama_name = entry["ollama_name"]
    derivation_type = entry.get("derivation_type", "unknown")
    scan_target = entry.get("provenance_scan_target")
    fallbacks = entry.get("provenance_scan_fallbacks", [])

    base_caveats = [
        "Provenance verified at upstream HF source; does not inspect local GGUF blob conversion"
    ]

    # --- Skip conditions ---
    if derivation_type == "cloud_only":
        return build_record(entry, {}, "N/A", "N_A", None,
                            "Cloud-only API proxy; no local weights to verify",
                            base_caveats + ["cloud_only: provenance N/A"])

    if derivation_type == "local_modelfile_derivative":
        base = entry.get("base_model", "unknown")
        return build_record(entry, {}, "N/A", "N_A", None,
                            f"Modelfile derivative of {base}; provenance inherited from base",
                            base_caveats + [f"Derivative: weights unchanged from {base}"])

    if scan_target is None:
        return build_record(entry, {}, "N/A", "UNKNOWN", None,
                            "No confirmed upstream HF ID; scan target is null",
                            base_caveats + ["upstream_hf_id not confirmed; manual verification required"])

    if derivation_type == "gemma2_gated" or entry.get("hf_id_confidence") == "gated_no_token":
        return build_record(entry, {}, scan_target, "N_A_GATED", None,
                            "HF_TOKEN required for gated model; not present in Vault secret/huggingface/admin",
                            base_caveats + ["google/gemma-2-27b-it is a gated HF model; provision HF_TOKEN to scan"])

    if dry_run:
        print(f"  [DRY-RUN] would scan: {ollama_name} → {scan_target}")
        return build_record(entry, {}, scan_target, "DRY_RUN", None,
                            "Dry run — not executed", base_caveats)

    # --- Try primary target, then fallbacks ---
    candidates = [scan_target] + fallbacks
    last_error = ""
    for candidate in candidates:
        print(f"  scanning {ollama_name} → {candidate} ...", flush=True)
        try:
            rc, output = run_scan(candidate)
        except subprocess.TimeoutExpired:
            last_error = f"timeout after 300s scanning {candidate}; model too large to scan on this host"
            print(f"    TIMEOUT on {candidate}")
            continue

        # rc=-9 means SIGKILL (OOM); rc=1 means kit-level error
        if rc == -9:
            last_error = (f"OOM-killed (SIGKILL) scanning {candidate}; "
                          f"model weights too large to load for signal extraction on Mac Mini 48GB")
            print(f"    OOM-KILLED on {candidate}")
            # Don't try fallbacks — same model, same OOM
            return build_record(entry, {}, candidate, "SCAN_OOM", None,
                                last_error,
                                base_caveats + [
                                    "Kit loads full model weights for signal extraction; "
                                    "model exceeds available RAM on Mac Mini",
                                    "Re-run on Mac Studio (96GB) or use --no-weight-signals flag if available"
                                ])

        # Check for 404 / repo not found
        if "404" in output or "Repository Not Found" in output or "does not exist" in output.lower():
            print(f"    404 on {candidate}, trying fallback...")
            last_error = f"HF repo not found: {candidate}"
            continue

        # rc=1 with no JSON = kit error (e.g., tokenizer parse failure)
        if rc != 0 and not output.strip().startswith("{"):
            # Extract error from stderr portion
            err_match = [l for l in output.splitlines() if "Error:" in l]
            err_detail = err_match[-1] if err_match else output[-200:]
            last_error = f"Kit error (rc={rc}) on {candidate}: {err_detail}"
            print(f"    kit error on {candidate}: {err_detail}")
            continue

        scan_data = extract_top_match(output)
        if not scan_data:
            last_error = f"Could not parse JSON output from scan of {candidate}"
            print(f"    parse error on {candidate}")
            continue

        # Successfully parsed — extract verdict
        matches = scan_data.get("matches", [])
        if not matches:
            verdict = "UNKNOWN"
            confidence = None
            reason = f"No matches returned from scan of {candidate}"
        else:
            top = matches[0]
            pipeline_score = top.get("scores", {}).get("pipeline_score", 0.0)
            provenance_decision = top.get("provenance_decision", "")
            confidence = pipeline_score

            if pipeline_score >= 0.85 or "Confirmed" in provenance_decision:
                verdict = "VERIFIED"
            elif pipeline_score >= 0.70:
                verdict = "LIKELY"
            elif pipeline_score >= 0.50:
                verdict = "WEAK_MATCH"
            else:
                verdict = "NO_MATCH"

            reason = f"{provenance_decision} (pipeline_score={pipeline_score:.3f}, hf_id={candidate})"

        caveats = list(base_caveats)
        if candidate != scan_target:
            caveats.append(f"Primary HF ID {scan_target} returned 404; used fallback {candidate}")

        return build_record(entry, scan_data, candidate, verdict, confidence, reason, caveats)

    # All candidates exhausted
    return build_record(entry, {}, scan_target, "UNKNOWN", None,
                        f"All HF ID candidates failed: {last_error}",
                        base_caveats + ["All primary and fallback HF IDs failed; manual verification required"])


def persist_record(record: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fname = f"{safe_model_filename(record['model_id'])}_{date_str}.json"
    out_path = OUTPUT_DIR / fname
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", help="Only scan this ollama_name")
    args = parser.parse_args()

    mapping = yaml.safe_load(MAPPING_FILE.read_text(encoding="utf-8"))
    models = mapping.get("ollama_models", [])

    if args.model:
        models = [m for m in models if m["ollama_name"] == args.model]
        if not models:
            print(f"No model '{args.model}' found in mapping.", file=sys.stderr)
            return 1

    # Special-case gemma2: check if HF_TOKEN is present
    import os
    hf_token = os.environ.get("HF_TOKEN", "")

    results = []
    for entry in models:
        name = entry["ollama_name"]
        # Mark gemma as gated-no-token if no HF_TOKEN
        if "gemma" in name.lower() and not hf_token:
            entry = dict(entry)
            entry["hf_id_confidence"] = "gated_no_token"

        print(f"\n[{name}]")
        record = scan_model(entry, dry_run=args.dry_run)
        out_path = persist_record(record)
        print(f"  verdict={record['verdict']} confidence={record['confidence']} → {out_path.name}")
        results.append(record)

    # Summary
    print("\n=== BACKFILL SUMMARY ===")
    for r in results:
        print(f"  {r['model_id']:50s} {r['verdict']:15s} {str(r['confidence'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
