"""Slack webhook notifier for executor and training events.

Configure via environment variable or .env file:
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
    SLACK_CHANNEL=#ai-builds          # optional override
    SLACK_USERNAME=AI Platform        # optional

Usage:
    from framework.slack_notifier import SlackNotifier
    notifier = SlackNotifier()
    notifier.post_completion("RM-UI-008", elapsed_seconds=142)
    notifier.post_failure("RM-DATA-006", error="aider timed out", retries=3)
    notifier.post_milestone(50, total=254)
    notifier.post_training_ready(example_count=10)

Standalone daemon:
    python3 framework/slack_notifier.py --watch
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
import urllib.request
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
GITHUB_REPO  = "https://github.com/adbcox/integrated-ai-platform"

MILESTONE_COUNTS = {25, 50, 100, 150, 200}


# ── Colour helpers for Slack mrkdwn ──────────────────────────────────────────

def _code(s: str) -> str:    return f"`{s}`"
def _bold(s: str) -> str:    return f"*{s}*"
def _link(text: str, url: str) -> str: return f"<{url}|{text}>"


class SlackNotifier:
    """Post rich Slack messages for platform events."""

    def __init__(
        self,
        webhook_url: str = "",
        channel: str = "#ai-builds",
        username: str = "AI Platform",
        icon_emoji: str = ":robot_face:",
        dry_run: bool = False,
    ) -> None:
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
        self.channel     = os.environ.get("SLACK_CHANNEL", channel)
        self.username    = os.environ.get("SLACK_USERNAME", username)
        self.icon_emoji  = icon_emoji
        self.dry_run     = dry_run or not self.webhook_url

        if not self.webhook_url and not dry_run:
            print("SlackNotifier: SLACK_WEBHOOK_URL not set — running in dry-run mode", file=sys.stderr)
            self.dry_run = True

    # ── Low-level post ────────────────────────────────────────────────────────

    def _post(self, payload: dict) -> bool:
        payload.setdefault("username",   self.username)
        payload.setdefault("icon_emoji", self.icon_emoji)
        if self.channel:
            payload.setdefault("channel", self.channel)

        if self.dry_run:
            print(f"[SLACK DRY-RUN] {json.dumps(payload, indent=2)}")
            return True

        try:
            data = json.dumps(payload).encode()
            req  = urllib.request.Request(
                self.webhook_url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status == 200
        except Exception as e:
            print(f"Slack post failed: {e}", file=sys.stderr)
            return False

    # ── Event messages ────────────────────────────────────────────────────────

    def post_completion(self, item_id: str, title: str = "", elapsed_seconds: float = 0) -> bool:
        elapsed = f" in {_fmt_sec(elapsed_seconds)}" if elapsed_seconds > 0 else ""
        gh_link = _link(item_id, f"{GITHUB_REPO}/search?q={item_id}")
        return self._post({
            "attachments": [{
                "color": "#00875A",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn",
                     "text": f"✅ *Completed* {gh_link}{elapsed}\n{title}"}},
                ],
                "footer": "AI Platform",
                "ts": str(int(time.time())),
            }]
        })

    def post_failure(self, item_id: str, error: str = "", retries: int = 0) -> bool:
        retry_note = f" after {retries} retr{'y' if retries==1 else 'ies'}" if retries > 0 else ""
        gh_link = _link(item_id, f"{GITHUB_REPO}/search?q={item_id}")
        logs_link = _link("View logs", f"{GITHUB_REPO}/blob/main/execution.log")
        return self._post({
            "attachments": [{
                "color": "#DE350B",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn",
                     "text": f"❌ *Failed* {gh_link}{retry_note}\n{_code(error[:200])}"}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": logs_link}]},
                ],
                "footer": "AI Platform",
                "ts": str(int(time.time())),
            }]
        })

    def post_milestone(self, count: int, total: int = 254) -> bool:
        pct   = round(count / total * 100)
        bar   = "█" * (pct // 10) + "░" * (10 - pct // 10)
        return self._post({
            "blocks": [
                {"type": "header", "text": {"type": "plain_text",
                 "text": f"🎉 Milestone: {count} items completed!"}},
                {"type": "section", "text": {"type": "mrkdwn",
                 "text": f"`{bar}` {pct}% complete ({count}/{total} items)"}},
                {"type": "context", "elements": [{"type": "mrkdwn",
                 "text": _link("View roadmap", f"{GITHUB_REPO}")}]},
            ]
        })

    def post_training_ready(self, example_count: int) -> bool:
        return self._post({
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "🎓 Training data ready!"}},
                {"type": "section", "text": {"type": "mrkdwn",
                 "text": (f"*{example_count}* quality training examples collected.\n"
                          f"Run `python3 web/dashboard/server.py` → click *Start Fine-Tuning*")}},
            ]
        })

    def post_training_complete(self, duration_seconds: float, example_count: int) -> bool:
        return self._post({
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "✅ Fine-tuning complete!"}},
                {"type": "section", "text": {"type": "mrkdwn",
                 "text": (f"Model trained on *{example_count}* examples in *{_fmt_sec(duration_seconds)}*.\n"
                          f"Deploy with: `ollama create qwen2.5-coder:custom`")}},
            ]
        })

    def post_system_error(self, message: str) -> bool:
        return self._post({
            "attachments": [{
                "color": "#DE350B",
                "blocks": [{"type": "section", "text": {"type": "mrkdwn",
                 "text": f"🚨 *System Error*\n{_code(message[:300])}"}}],
                "ts": str(int(time.time())),
            }]
        })

    def post_daily_digest(self, completions: int, failures: int, quality_examples: int) -> bool:
        today = datetime.date.today().strftime("%A, %B %-d")
        return self._post({
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": f"📊 Daily Digest — {today}"}},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*Completions*\n{completions}"},
                    {"type": "mrkdwn", "text": f"*Failures*\n{failures}"},
                    {"type": "mrkdwn", "text": f"*Training examples*\n{quality_examples}"},
                ]},
            ]
        })


# ── Standalone watcher ────────────────────────────────────────────────────────

def _fmt_sec(s: float) -> str:
    if s < 60: return f"{int(s)}s"
    h = int(s // 3600); m = int((s % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


class _LogWatcher:
    def __init__(self) -> None:
        self._sizes: dict[str, int] = {}
        self._seen_completions: set[str] = set()
        self._seen_failures:    set[str] = set()
        self._sft_posted  = False
        self._announced_milestones: set[int] = set()
        self._total = 0

    def poll(self, notifier: SlackNotifier) -> None:
        for path_str in LOG_CANDIDATES:
            p = Path(path_str)
            if not p.exists(): continue
            size = p.stat().st_size
            prev = self._sizes.get(path_str, 0)
            if size <= prev: continue
            with p.open(errors="replace") as f:
                f.seek(prev); chunk = f.read()
            self._sizes[path_str] = size

            for m in re.finditer(r"✅ Completed: (\S+)", chunk):
                item = m.group(1)
                if item not in self._seen_completions:
                    self._seen_completions.add(item)
                    self._total += 1
                    notifier.post_completion(item, elapsed_seconds=0)

            for m in re.finditer(r"❌ Failed.*?(RM-\S+).*?:\s*(.+)", chunk, re.I):
                item = m.group(1)
                if item not in self._seen_failures:
                    self._seen_failures.add(item)
                    notifier.post_failure(item, error=m.group(2)[:200])

            if re.search(r"SHUTDOWN|Traceback.*crash", chunk, re.I):
                notifier.post_system_error("Executor crashed — check logs")

        for milestone in sorted(MILESTONE_COUNTS):
            if self._total >= milestone and milestone not in self._announced_milestones:
                self._announced_milestones.add(milestone)
                notifier.post_milestone(milestone)

        if not self._sft_posted:
            try:
                sys.path.insert(0, str(REPO_ROOT))
                from framework.learning_analytics import analyze_training_data
                r = analyze_training_data()
                count = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
                if count >= 10:
                    self._sft_posted = True
                    notifier.post_training_ready(count)
            except Exception:
                pass


def _watch(notifier: SlackNotifier, poll_seconds: int) -> None:
    watcher   = _LogWatcher()
    last_digest_day: Optional[int] = None

    print(f"Slack notifier started (poll={poll_seconds}s, dry_run={notifier.dry_run})")
    notifier._post({"text": "🤖 AI Platform Slack notifier started"})

    while True:
        try:
            watcher.poll(notifier)
            now = datetime.datetime.now()
            if now.hour == 9 and now.day != last_digest_day:
                last_digest_day = now.day
                try:
                    sys.path.insert(0, str(REPO_ROOT))
                    from framework.learning_analytics import analyze_training_data
                    r   = analyze_training_data()
                    qual = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
                except Exception:
                    qual = 0
                notifier.post_daily_digest(
                    completions=watcher._total,
                    failures=len(watcher._seen_failures),
                    quality_examples=qual,
                )
        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)
        time.sleep(poll_seconds)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Slack notifier daemon")
    parser.add_argument("--watch",     action="store_true", help="Start watching executor logs")
    parser.add_argument("--dry-run",   action="store_true", help="Print payloads, don't send")
    parser.add_argument("--poll",      type=int, default=15, help="Poll interval (seconds)")
    parser.add_argument("--webhook",   default="", help="Override SLACK_WEBHOOK_URL")
    parser.add_argument("--test",      action="store_true", help="Send a test message and exit")
    args = parser.parse_args()

    notifier = SlackNotifier(webhook_url=args.webhook, dry_run=args.dry_run)

    if args.test:
        ok = notifier._post({"text": "🧪 Test message from AI Platform Slack notifier"})
        print("OK" if ok else "FAILED")
        return

    if args.watch:
        _watch(notifier, args.poll)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
