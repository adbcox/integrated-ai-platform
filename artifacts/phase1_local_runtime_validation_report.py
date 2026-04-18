#!/usr/bin/env python3
"""Phase 1 baseline local runtime validation report entrypoint.

Deterministic CLI that runs the Phase 1 baseline validation pack
against a scratch base root and prints/returns the normalized outcome.

Does not require a live Ollama daemon; the inference gateway uses its
local stub executor by default. The point of this report is to
exercise the full local-route shape (profile -> gateway -> workspace
-> wrapped command -> artifact bundle) and emit a reproducible
manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.runtime_validation_pack import run_baseline_validation  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 baseline local runtime validation report")
    parser.add_argument("--base-root", default="", help="scratch/artifact base root (default: tmp)")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--session-id", default="phase1-baseline")
    parser.add_argument("--json", action="store_true", help="emit full JSON report on stdout")
    args = parser.parse_args(argv)

    if args.base_root:
        base_root = Path(args.base_root)
    else:
        base_root = Path(tempfile.mkdtemp(prefix="phase1-runtime-validate-"))
    run_id = args.run_id or f"run-{uuid4().hex[:12]}"

    result = run_baseline_validation(
        source_root=REPO_ROOT,
        base_root=base_root,
        run_id=run_id,
        session_id=args.session_id,
    )

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2, ensure_ascii=False))
    else:
        print(f"phase1 local runtime validation: success={result.success}")
        print(f"manifest: {result.manifest_path}")
        print(f"profile: {result.inference.profile_name}")
        print(f"final_outcome: {result.manifest.final_outcome}")
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
