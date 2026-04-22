"""
Command runner: bounded command execution with whitelist enforcement.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union


ALLOWED_COMMANDS = {
    "python3",
    "python",
    "ls",
    "find",
    "cat",
    "head",
    "tail",
    "grep",
    "sort",
    "uniq",
    "wc",
    "file",
    "pwd",
    "make",
    "yaml-lint",
}


def execute_command(
    command: List[str],
    cwd: Optional[Union[str, Path]] = None,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Execute a command with whitelist enforcement and timeout.

    Args:
        command: Command as list of strings (e.g., ["ls", "-la"])
        cwd: Working directory for command execution
        timeout_seconds: Timeout in seconds

    Returns:
        Result dict with command, allowed, exit_code, stdout, stderr, duration_seconds, timed_out
    """
    if not command or len(command) == 0:
        return {
            "command": [],
            "allowed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Empty command",
            "duration_seconds": 0,
            "cwd": str(cwd) if cwd else None,
            "timed_out": False
        }

    base_command = command[0]

    if base_command not in ALLOWED_COMMANDS:
        return {
            "command": command,
            "allowed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command '{base_command}' not in whitelist",
            "duration_seconds": 0,
            "cwd": str(cwd) if cwd else None,
            "timed_out": False
        }

    start_time = time.time()
    stdout_output = ""
    stderr_output = ""
    exit_code = -1
    timed_out = False

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            text=True
        )

        stdout_output = result.stdout[:5000]
        stderr_output = result.stderr[:5000]
        exit_code = result.returncode

    except subprocess.TimeoutExpired:
        timed_out = True
        stderr_output = f"Command timed out after {timeout_seconds}s"
        exit_code = -1

    except Exception as e:
        exit_code = -1
        stderr_output = str(e)

    duration = time.time() - start_time

    return {
        "command": command,
        "allowed": True,
        "exit_code": exit_code,
        "stdout": stdout_output,
        "stderr": stderr_output,
        "duration_seconds": round(duration, 3),
        "cwd": str(cwd) if cwd else None,
        "timed_out": timed_out
    }


if __name__ == "__main__":
    result = execute_command(["ls", "-la"], timeout_seconds=5)
    print(f"✓ Command executed: {result['command']}")
    print(f"  Exit code: {result['exit_code']}")
    print(f"  Allowed: {result['allowed']}")

    result = execute_command(["rm", "-rf", "/"], timeout_seconds=5)
    print(f"\n✓ Dangerous command blocked: {result['command']}")
    print(f"  Allowed: {result['allowed']}")
