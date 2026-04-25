#!/usr/bin/env python3
"""macOS voice notification daemon for autonomous executor events.

Uses the built-in `say` command — no dependencies required.

Usage:
    python3 bin/voice_notifier.py                    # watch executor logs
    python3 bin/voice_notifier.py --voice Samantha   # pick voice
    python3 bin/voice_notifier.py --quiet-hours 23-7  # suppress 11pm–7am
    python3 bin/voice_notifier.py --dry-run          # print speech, don't speak
    python3 bin/voice_notifier.py --list-voices      # show installed voices
"""
from __future__ import annotations

import argparse
import datetime
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

TRAINING_LOG = "/tmp/training_cycle.log"
POLL_INTERVAL = 15   # seconds between log checks
RATE_LIMIT     = 60  # minimum seconds between any two speech events

MILESTONE_COUNTS = {25, 50, 100, 150, 200}

# Priority levels
PRI_CRITICAL = 3   # always speak, even in quiet hours
PRI_HIGH     = 2   # speak unless quiet hours active
PRI_NORMAL   = 1   # speak unless quiet hours active


# ── Speech ────────────────────────────────────────────────────────────────────

def list_voices() -> list[str]:
    """Return installed macOS voices."""
    r = subprocess.run(["say", "--voice=?"], capture_output=True, text=True)
    return [line.split()[0] for line in r.stdout.splitlines() if line.strip()]


def speak(text: str, voice: str, rate: int = 175, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[VOICE] {text}")
        return
    try:
        subprocess.Popen(
            ["say", "--voice", voice, "--rate", str(rate), text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"say failed: {e}", file=sys.stderr)


def _rm_id_to_speech(rm_id: str) -> str:
    """Convert 'RM-UI-008' to 'R M U I 0 0 8' (clearly spoken)."""
    parts = rm_id.replace("RM-", "").split("-")
    out = "R M"
    for part in parts:
        out += " " + " ".join(part)
    return out


# ── Quiet hours ───────────────────────────────────────────────────────────────

def _in_quiet_hours(quiet_range: Optional[tuple[int, int]]) -> bool:
    if not quiet_range:
        return False
    start, end = quiet_range
    hour = datetime.datetime.now().hour
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


# ── Milestone tracker ─────────────────────────────────────────────────────────

class MilestoneTracker:
    def __init__(self) -> None:
        self._announced: set[int] = set()

    def check(self, count: int) -> Optional[str]:
        for m in sorted(MILESTONE_COUNTS):
            if count >= m and m not in self._announced:
                self._announced.add(m)
                pct = round(m / 254 * 100)
                return f"{m} items completed. {pct} percent done. Keep going!"
        return None


# ── Log watcher ───────────────────────────────────────────────────────────────

class LogWatcher:
    def __init__(self, paths: list[str]) -> None:
        self._sizes: dict[str, int] = {}
        self._paths = paths
        self._seen_completions: set[str] = set()
        self._seen_failures:    set[str] = set()
        self._sft_notified = False
        self._total_completions = 0

    def _active(self) -> list[Path]:
        return [Path(p) for p in self._paths if Path(p).exists()]

    def poll(self) -> list[tuple[str, int]]:
        """Return list of (speech_text, priority)."""
        events: list[tuple[str, int]] = []

        for log_path in self._active():
            size = log_path.stat().st_size
            prev = self._sizes.get(str(log_path), 0)
            if size <= prev:
                continue
            with log_path.open(errors="replace") as f:
                f.seek(prev)
                new_text = f.read()
            self._sizes[str(log_path)] = size

            # Completions
            for m in re.finditer(r"✅ Completed: (\S+)", new_text):
                item = m.group(1)
                if item not in self._seen_completions:
                    self._seen_completions.add(item)
                    self._total_completions += 1
                    rm = _rm_id_to_speech(item) if item.startswith("RM-") else item
                    events.append((f"{rm} completed.", PRI_NORMAL))

            # Failures
            for m in re.finditer(r"❌ Failed.*?(RM-\S+)", new_text):
                item = m.group(1)
                if item not in self._seen_failures:
                    self._seen_failures.add(item)
                    rm = _rm_id_to_speech(item)
                    retries_m = re.search(r"after (\d+) retr", new_text, re.I)
                    retries = f" after {retries_m.group(1)} retries" if retries_m else ""
                    events.append((f"{rm} failed{retries}. Check the logs.", PRI_CRITICAL))

            # Executor crash
            if re.search(r"SHUTDOWN|Traceback|Exception.*crash", new_text, re.I):
                events.append(("Executor crashed. Check the logs immediately.", PRI_CRITICAL))

        # Training readiness
        if not self._sft_notified:
            try:
                sys.path.insert(0, str(REPO_ROOT))
                from framework.learning_analytics import analyze_training_data
                r = analyze_training_data()
                count = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
                if count >= 10:
                    self._sft_notified = True
                    events.append((f"Ten quality examples collected. Ready for fine tuning.", PRI_HIGH))
            except Exception:
                pass

        # Training progress
        train_log = Path(TRAINING_LOG)
        if train_log.exists():
            prev = self._sizes.get(TRAINING_LOG, 0)
            size = train_log.stat().st_size
            if size > prev:
                with train_log.open(errors="replace") as f:
                    f.seek(prev)
                    chunk = f.read()
                self._sizes[TRAINING_LOG] = size
                if re.search(r"Saved adapter|Training complete|Done", chunk):
                    events.append(("Fine tuning complete. Custom model is ready to deploy.", PRI_HIGH))

        return events, self._total_completions


# ── Daily digest ──────────────────────────────────────────────────────────────

class DailyDigest:
    def __init__(self) -> None:
        self._last_day: Optional[int] = None

    def check(self, total_completions: int) -> Optional[str]:
        now = datetime.datetime.now()
        if now.hour != 9 or now.day == self._last_day:
            return None
        self._last_day = now.day
        try:
            sys.path.insert(0, str(REPO_ROOT))
            from framework.learning_analytics import analyze_training_data
            r = analyze_training_data()
            qual = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
        except Exception:
            qual = 0
        return (
            f"Good morning. Daily update: {total_completions} items completed in the executor. "
            f"{qual} quality training examples collected."
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="macOS voice notifier for executor events")
    parser.add_argument("--voice",        default="Samantha", help="macOS voice name")
    parser.add_argument("--rate",         type=int, default=175, help="Speech rate (words/min)")
    parser.add_argument("--quiet-hours",  default="23-7", help="Silent range, e.g. 23-7")
    parser.add_argument("--dry-run",      action="store_true", help="Print instead of speaking")
    parser.add_argument("--poll",         type=int, default=POLL_INTERVAL, help="Poll interval (seconds)")
    parser.add_argument("--list-voices",  action="store_true", help="List installed voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        for v in list_voices():
            print(v)
        return

    quiet_range: Optional[tuple[int, int]] = None
    if args.quiet_hours:
        parts = args.quiet_hours.split("-")
        if len(parts) == 2:
            try:
                quiet_range = (int(parts[0]), int(parts[1]))
            except ValueError:
                pass

    watcher   = LogWatcher(LOG_CANDIDATES)
    milestone = MilestoneTracker()
    digest    = DailyDigest()
    last_spoken_at = 0.0

    print(f"Voice notifier started — voice={args.voice}, rate={args.rate}, quiet={args.quiet_hours}")
    print(f"Watching: {', '.join(LOG_CANDIDATES)}")
    if args.dry_run:
        print("[dry-run — text printed, not spoken]")

    speak("AI Platform voice notifier started.", args.voice, args.rate, args.dry_run)

    while True:
        try:
            quiet = _in_quiet_hours(quiet_range)
            events, total = watcher.poll()

            # Check milestone
            msg = milestone.check(total)
            if msg:
                events.append((msg, PRI_HIGH))

            # Daily digest
            dmsg = digest.check(total)
            if dmsg:
                events.append((dmsg, PRI_NORMAL))

            now = time.time()
            for text, priority in events:
                if quiet and priority < PRI_CRITICAL:
                    print(f"[quiet] Suppressed: {text}")
                    continue
                if now - last_spoken_at < RATE_LIMIT and priority < PRI_CRITICAL:
                    print(f"[rate-limited] Would say: {text}")
                    continue
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"{ts}  [{priority}] {text}")
                speak(text, args.voice, args.rate, args.dry_run)
                last_spoken_at = time.time()

        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)

        time.sleep(args.poll)


if __name__ == "__main__":
    main()
