#!/usr/bin/env python3
"""macOS notification daemon for autonomous executor events.

Watches execution logs and fires macOS notifications on significant events.
Uses osascript — no dependencies, works on any Mac.

Usage:
    python3 bin/notify_daemon.py              # watch all /tmp/executor*.log files
    python3 bin/notify_daemon.py --quiet-hours 23-7  # suppress 11pm-7am
    python3 bin/notify_daemon.py --dry-run    # print what would be sent

Significant events:
    ✅  Item completed      → notification
    ❌  Item failed         → notification (always, ignores quiet hours)
    🎓  SFT threshold hit   → notification + sound
    📊  Daily digest         → summary at 9am
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
LOG_CANDIDATES = [
    "/tmp/executor_longrun.log",
    "/tmp/executor_overnight.log",
    "/tmp/executor_clean_run.log",
    "/tmp/executor_3items.log",
]
POLL_SECONDS = 10
SFT_THRESHOLD = 10


# ── macOS notification helper ─────────────────────────────────────────────────

def notify(title: str, message: str, sound: str = "", dry_run: bool = False) -> None:
    if dry_run:
        print(f"[NOTIFY] {title}: {message}")
        return
    sound_clause = f' sound name "{sound}"' if sound else ""
    script = (
        f'display notification "{message}" '
        f'with title "{title}"{sound_clause}'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=5,
        )
    except Exception as e:
        print(f"notify failed: {e}", file=sys.stderr)


# ── Quiet hours ───────────────────────────────────────────────────────────────

def _in_quiet_hours(quiet_range: Optional[tuple[int, int]]) -> bool:
    if not quiet_range:
        return False
    start, end = quiet_range
    hour = datetime.datetime.now().hour
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # wraps midnight


# ── Log watching ──────────────────────────────────────────────────────────────

class LogWatcher:
    def __init__(self, paths: list[str]) -> None:
        self._sizes: dict[str, int] = {}
        self._paths = paths
        self._seen_completions: set[str] = set()
        self._seen_failures: set[str] = set()
        self._sft_notified = False

    def _active_logs(self) -> list[Path]:
        return [Path(p) for p in self._paths if Path(p).exists()]

    def poll(self, quiet: bool, dry_run: bool) -> list[tuple[str, str, str]]:
        """Return list of (title, message, sound) for new events."""
        events: list[tuple[str, str, str]] = []
        for log_path in self._active_logs():
            size = log_path.stat().st_size
            prev = self._sizes.get(str(log_path), 0)
            if size <= prev:
                continue
            # Read only new bytes
            with log_path.open(errors="replace") as f:
                f.seek(prev)
                new_text = f.read()
            self._sizes[str(log_path)] = size

            # Completed items
            for m in re.finditer(r"✅ Completed: (\S+)", new_text):
                item = m.group(1)
                if item not in self._seen_completions:
                    self._seen_completions.add(item)
                    if not quiet:
                        events.append(("✅ Item Completed", item, ""))

            # Failed items (always notify, even in quiet hours)
            for m in re.finditer(r"❌ Failed.*?(\S+)", new_text):
                item = m.group(1)
                if item not in self._seen_failures:
                    self._seen_failures.add(item)
                    events.append(("❌ Executor Failure", item, "Basso"))

            # Training threshold
            if not self._sft_notified:
                try:
                    sys.path.insert(0, str(REPO_ROOT))
                    from framework.learning_analytics import analyze_training_data
                    r = analyze_training_data()
                    count = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
                    if count >= SFT_THRESHOLD:
                        self._sft_notified = True
                        events.append(("🎓 Training Ready!", f"{count} quality examples — SFT threshold reached", "Glass"))
                except Exception:
                    pass

        return events


# ── Daily digest ──────────────────────────────────────────────────────────────

class DailyDigest:
    def __init__(self) -> None:
        self._last_day: Optional[int] = None

    def check(self, dry_run: bool) -> None:
        now = datetime.datetime.now()
        if now.hour != 9 or now.day == self._last_day:
            return
        self._last_day = now.day
        try:
            sys.path.insert(0, str(REPO_ROOT))
            import web.dashboard.server as srv
            s = srv._build_status()
            rm = s.get("roadmap", {})
            done = (rm.get("completed", 0) + rm.get("accepted", 0))
            total = rm.get("total", 254)
            qual = s.get("training", {}).get("quality_examples", 0)
            msg = f"{done}/{total} items done · {qual} training examples"
            notify("📊 Daily Digest", msg, dry_run=dry_run)
        except Exception as e:
            print(f"digest error: {e}", file=sys.stderr)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="macOS notification daemon for executor events")
    parser.add_argument("--quiet-hours", default="23-7",
                        help="Suppress non-critical alerts during these hours (default: 23-7)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print notifications instead of displaying them")
    parser.add_argument("--poll", type=int, default=POLL_SECONDS,
                        help="Polling interval in seconds")
    args = parser.parse_args()

    # Parse quiet hours
    quiet_range: Optional[tuple[int, int]] = None
    if args.quiet_hours:
        parts = args.quiet_hours.split("-")
        if len(parts) == 2:
            try:
                quiet_range = (int(parts[0]), int(parts[1]))
            except ValueError:
                pass

    watcher = LogWatcher(LOG_CANDIDATES)
    digest  = DailyDigest()

    print(f"Notification daemon started (poll={args.poll}s, quiet={args.quiet_hours})")
    print(f"Watching: {', '.join(LOG_CANDIDATES)}")
    if args.dry_run:
        print("[dry-run mode — notifications printed, not displayed]")

    notify("AI Platform", "Notification daemon started", dry_run=args.dry_run)

    while True:
        try:
            quiet = _in_quiet_hours(quiet_range)
            events = watcher.poll(quiet=quiet, dry_run=args.dry_run)
            for title, msg, sound in events:
                notify(title, msg, sound=sound, dry_run=args.dry_run)
                print(f"{datetime.datetime.now():%H:%M:%S}  {title}: {msg}")
            digest.check(dry_run=args.dry_run)
        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
