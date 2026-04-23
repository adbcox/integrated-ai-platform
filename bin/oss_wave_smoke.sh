#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "[1/5] OpenHands config smoke"
bin/oss_wave_openhands.sh validate-config

echo "[2/5] MCP registry smoke"
bin/oss_wave_mcp.sh smoke

echo "[3/5] MarkItDown wrapper syntax"
python3 -m py_compile bin/markitdown_wrapper.py

echo "[4/5] PR-Agent wrapper syntax"
sh -n bin/oss_wave_pr_agent.sh

echo "[5/5] Status probe"
python3 bin/oss_wave_status.py >/tmp/oss_wave_status.json
cat /tmp/oss_wave_status.json

echo "PASS: first-wave smoke checks completed"
