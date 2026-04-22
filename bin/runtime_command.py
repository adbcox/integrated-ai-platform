#!/usr/bin/env python3
"""
Command execution layer for bounded runtime.
Executes shell commands safely and returns structured results.
"""

import subprocess
import json
import sys
import time
from typing import Dict, Any


def execute_command(command: str, timeout: int = 30, cwd: str = None) -> Dict[str, Any]:
    """
    Execute a shell command and return structured result.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default 30)
        cwd: Working directory (default current)

    Returns:
        Dictionary with command, stdout, stderr, return_code, duration_ms
    """
    start_time = time.time()

    result = {
        "command": command,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "duration_ms": 0
    }

    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )

        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["return_code"] = process.returncode

    except subprocess.TimeoutExpired:
        result["stderr"] = f"Command timeout after {timeout} seconds"
        result["return_code"] = 124
    except Exception as e:
        result["stderr"] = f"Command execution error: {str(e)}"
        result["return_code"] = 1
    finally:
        result["duration_ms"] = int((time.time() - start_time) * 1000)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 runtime_command.py '<command>'")
        sys.exit(1)

    command = sys.argv[1]
    result = execute_command(command)
    print(json.dumps(result, indent=2))
