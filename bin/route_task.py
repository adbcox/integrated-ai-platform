#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.router import TaskRouter


def main():
    if len(sys.argv) < 2:
        print("Usage: route_task.py 'description' [file1 file2...]")
        return 1

    router = TaskRouter(Path.cwd())
    route = router.classify(sys.argv[1], sys.argv[2:] if len(sys.argv) > 2 else None)

    print(f"Executor: {route.executor.value}")
    print(f"Model: {route.model}")
    print(f"Confidence: {route.confidence}")
    print(f"Reasoning: {route.reasoning}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
