#!/usr/bin/env python3
"""Self-healing media pipeline daemon.

Usage:
    python3 bin/selfheal.py --check              # one-shot check, print report
    python3 bin/selfheal.py --fix                # check + apply all auto-fixes
    python3 bin/selfheal.py --daemon             # run every 5 min indefinitely
    python3 bin/selfheal.py --diagnose "issue"   # AI diagnosis via Ollama
    python3 bin/selfheal.py --config             # show *arr config summary
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.health_checker import MediaHealthChecker, HealthReport
from framework.auto_fixer     import AutoFixer
from framework.heal_log       import log_check, log_fix, log_issue, tail, recent_fixes


# ── Daemon state (shared with server.py when imported) ───────────────────────

_daemon_state: dict = {
    "running":      False,
    "last_run_at":  None,
    "last_report":  None,
    "next_run_in":  None,
    "cycle_count":  0,
}

DAEMON_INTERVAL = int(os.environ.get("SELFHEAL_INTERVAL", "300"))   # 5 min default


# ── Core heal cycle ───────────────────────────────────────────────────────────

def run_heal_cycle(apply_fixes: bool = True) -> dict:
    """Run one full check + optional fix cycle. Returns the report dict."""
    checker = MediaHealthChecker()
    t0 = time.monotonic()
    report  = checker.run()

    # Log all issues
    for issue in report.issues:
        log_issue(issue.service, issue.severity, issue.message, issue.fixable)

    fix_results = []
    if apply_fixes and report.fixable:
        fixer = AutoFixer()
        results = fixer.apply_all(report.fixable)
        for r in results:
            log_fix("auto", r.action, r.detail, r.ok, r.error)
            fix_results.append(r.as_dict())

    log_check("all", len(report.issues), len(fix_results), time.monotonic() - t0)

    out = report.as_dict()
    out["fixes_applied"] = fix_results
    return out


# ── AI diagnosis ──────────────────────────────────────────────────────────────

def ai_diagnose(issue_description: str, context: dict | None = None) -> dict:
    """Ask Ollama to diagnose an issue and suggest fixes."""
    ollama_host = os.environ.get("OLLAMA_HOST", "localhost:11434")
    if "://" not in ollama_host:
        ollama_host = f"http://{ollama_host}"

    ctx_text = ""
    if context:
        ctx_text = f"\n\nSystem context:\n{json.dumps(context, indent=2)}"

    prompt = f"""You are a homelab media server expert. Diagnose this issue and give a concise fix.

Issue: {issue_description}{ctx_text}

Respond in this exact format:
ROOT CAUSE: (1-2 sentences explaining why this happened)
FIX STEPS:
1. (first step)
2. (second step)
3. (etc.)
VERIFY: (1 sentence on how to confirm the fix worked)
AUTO-FIXABLE: yes/no"""

    payload = json.dumps({
        "model":  os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 400},
    }).encode()

    try:
        req = urllib.request.Request(
            f"{ollama_host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            result   = json.loads(resp.read())
            response = result.get("response", "").strip()

        # Parse structured response
        lines = response.splitlines()
        root_cause = ""
        fix_steps: list[str] = []
        verify = ""
        auto_fixable = False
        section = None
        for line in lines:
            line = line.strip()
            if line.startswith("ROOT CAUSE:"):
                section    = "root"
                root_cause = line[len("ROOT CAUSE:"):].strip()
            elif line.startswith("FIX STEPS:"):
                section = "fix"
            elif line.startswith("VERIFY:"):
                section = "verify"
                verify  = line[len("VERIFY:"):].strip()
            elif line.startswith("AUTO-FIXABLE:"):
                auto_fixable = "yes" in line.lower()
            elif section == "root" and line and not root_cause:
                root_cause = line
            elif section == "fix" and line and (line[0].isdigit() or line.startswith("-")):
                fix_steps.append(line.lstrip("0123456789.-) ").strip())
            elif section == "verify" and line and not verify:
                verify = line

        return {
            "issue":       issue_description,
            "root_cause":  root_cause or response[:200],
            "fix_steps":   fix_steps,
            "verify":      verify,
            "auto_fixable": auto_fixable,
            "raw":         response,
            "model":       result.get("model", ""),
        }
    except urllib.error.URLError:
        return {"error": "Ollama not reachable", "issue": issue_description}
    except Exception as exc:
        return {"error": str(exc)[:120], "issue": issue_description}


# ── Daemon loop ───────────────────────────────────────────────────────────────

def run_daemon(interval: int = DAEMON_INTERVAL) -> None:
    """Run heal cycles indefinitely. Intended to be called from a thread."""
    _daemon_state["running"] = True
    print(f"[selfheal] Daemon started (interval={interval}s)", flush=True)

    while _daemon_state["running"]:
        t_start = time.monotonic()
        try:
            print(f"[selfheal] Starting heal cycle #{_daemon_state['cycle_count'] + 1}", flush=True)
            report = run_heal_cycle(apply_fixes=True)
            _daemon_state["last_run_at"]  = time.time()
            _daemon_state["last_report"]  = report
            _daemon_state["cycle_count"] += 1
            n_issues = report.get("counts", {}).get("total", 0)
            n_fixes  = len(report.get("fixes_applied", []))
            print(f"[selfheal] Cycle done: {n_issues} issues, {n_fixes} fixes applied", flush=True)
        except Exception as exc:
            print(f"[selfheal] Cycle error: {exc}", flush=True)

        elapsed = time.monotonic() - t_start
        sleep_for = max(0, interval - elapsed)
        _daemon_state["next_run_in"] = sleep_for
        time.sleep(sleep_for)

    _daemon_state["running"] = False


def start_daemon_thread(interval: int = DAEMON_INTERVAL):
    """Start the daemon in a background thread. Returns the thread."""
    import threading
    t = threading.Thread(target=run_daemon, args=(interval,), daemon=True, name="selfheal")
    t.start()
    return t


def stop_daemon() -> None:
    _daemon_state["running"] = False


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_report(report: dict) -> None:
    counts = report.get("counts", {})
    dur    = report.get("duration_s", 0)
    print(f"\n{'='*60}")
    print(f"Health Check — {counts.get('total',0)} issues found in {dur:.1f}s")
    print(f"  Critical: {counts.get('critical',0)}  Warnings: {counts.get('warnings',0)}"
          f"  Fixable: {counts.get('fixable',0)}")
    print(f"Services: {report.get('services', {})}")

    issues = report.get("issues", [])
    if issues:
        print("\nIssues:")
        for iss in issues:
            icon = "🔴" if iss["severity"] == "critical" else "🟡" if iss["severity"] == "warning" else "ℹ️"
            fix  = " [AUTO-FIX]" if iss["fixable"] else ""
            print(f"  {icon} [{iss['service'].upper()}] {iss['message']}{fix}")
            if iss.get("detail"):
                print(f"       {iss['detail'][:80]}")

    fixes = report.get("fixes_applied", [])
    if fixes:
        print(f"\nFixes applied ({len(fixes)}):")
        for f in fixes:
            icon = "✅" if f["ok"] else "❌"
            print(f"  {icon} {f['action']}: {f['detail']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Media pipeline self-healing daemon")
    parser.add_argument("--check",    action="store_true", help="Run one-shot check (no fixes)")
    parser.add_argument("--fix",      action="store_true", help="Run one-shot check + apply fixes")
    parser.add_argument("--daemon",   action="store_true", help="Run continuously (every 5 min)")
    parser.add_argument("--diagnose", metavar="ISSUE",     help="AI diagnosis via Ollama")
    parser.add_argument("--config",   action="store_true", help="Show *arr config summary")
    parser.add_argument("--history",  action="store_true", help="Show recent healing history")
    parser.add_argument("--interval", type=int, default=DAEMON_INTERVAL,
                        help=f"Daemon interval in seconds (default: {DAEMON_INTERVAL})")
    args = parser.parse_args()

    if args.check:
        report = run_heal_cycle(apply_fixes=False)
        _print_report(report)

    elif args.fix:
        report = run_heal_cycle(apply_fixes=True)
        _print_report(report)

    elif args.daemon:
        try:
            run_daemon(interval=args.interval)
        except KeyboardInterrupt:
            print("\n[selfheal] Stopped")

    elif args.diagnose:
        print(f"Asking Ollama to diagnose: {args.diagnose!r}")
        result = ai_diagnose(args.diagnose)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\nROOT CAUSE:\n  {result['root_cause']}")
            print(f"\nFIX STEPS:")
            for i, step in enumerate(result["fix_steps"], 1):
                print(f"  {i}. {step}")
            print(f"\nVERIFY:\n  {result['verify']}")
            print(f"\nAUTO-FIXABLE: {'Yes' if result['auto_fixable'] else 'No'}")

    elif args.config:
        fixer = AutoFixer()
        summary = fixer.get_arr_config_summary()
        print(json.dumps(summary, indent=2))

    elif args.history:
        events = tail(50)
        for e in reversed(events):
            t = e.get("type", "")
            ts = e.get("ts", "")[:19]
            if t == "fix":
                icon = "✅" if e.get("ok") else "❌"
                print(f"  {ts} {icon} FIX [{e.get('service')}] {e.get('action')}: {e.get('detail','')[:60]}")
            elif t == "issue":
                sev = e.get("severity", "")
                icon = "🔴" if sev == "critical" else "🟡" if sev == "warning" else "ℹ️"
                print(f"  {ts} {icon} ISSUE [{e.get('service')}] {e.get('message','')[:60]}")
            elif t == "check":
                print(f"  {ts} 🔍 CHECK: {e.get('issue_count',0)} issues, "
                      f"{e.get('fix_count',0)} fixes, {e.get('duration_s',0)}s")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
