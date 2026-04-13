#!/usr/bin/env python3
"""Inject a tactical bootstrap message before handing aider to the operator."""
import argparse
import os
import re
import sys

import pexpect

BOOTSTRAP_MESSAGE = (
    "You are the tactical executor inside a frozen local-first development workflow.\n"
    "Stay within the files already added to chat.\n"
    "Do not widen scope.\n"
    "Do not edit until explicitly asked."
)

PROMPT_PATTERNS = [
    re.compile(rb"\(aider\)[^\n>]*> "),
    re.compile(rb"\(auto\)[^\n>]*> "),
    re.compile(rb"\(shell\)[^\n>]*> "),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap aider with a fixed system reminder.")
    parser.add_argument(
        "--prompt-timeout",
        type=float,
        default=float(os.environ.get("AIDER_BOOTSTRAP_PROMPT_TIMEOUT", 60)),
        help="Seconds to wait for the first aider prompt before injecting (default: 60)",
    )
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute (use -- before aider args)")
    args = parser.parse_args()
    if args.cmd and args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    if not args.cmd:
        parser.error("No aider command provided. Usage: aider_bootstrap.py -- <cmd ...>")
    return args


def wait_for_prompt(child: pexpect.spawn, timeout: float) -> None:
    if timeout <= 0:
        return
    try:
        child.expect_list(PROMPT_PATTERNS, timeout=timeout)
    except pexpect.TIMEOUT:
        return
    except pexpect.EOF:
        child.close()
        code = child.exitstatus if child.exitstatus is not None else 1
        sys.exit(code)


def main() -> None:
    args = parse_args()
    child = pexpect.spawn(
        args.cmd[0],
        args.cmd[1:],
        encoding=None,  # operate in bytes mode to avoid str/bytes mismatches
        timeout=None,
    )
    child.delaybeforesend = 0.05
    child.logfile = sys.stdout.buffer
    wait_for_prompt(child, args.prompt_timeout)
    child.sendline(BOOTSTRAP_MESSAGE.encode("utf-8"))
    try:
        child.interact(escape_character=None)
    finally:
        child.close()
    if child.signalstatus is not None:
        os.kill(os.getpid(), child.signalstatus)
    exit_code = child.exitstatus if child.exitstatus is not None else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
