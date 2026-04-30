#!/bin/bash
PROBLEM="$1"
if [ -z "$PROBLEM" ]; then
  echo "Usage: troubleshoot 'problem description'" >&2
  exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${TROUBLESHOOT_TEMPLATE:-$SCRIPT_DIR/troubleshoot-agent-v2.txt}"
# Use python for safe substitution (no sed metachar issues)
python3 -c "
import sys
tpl = open(sys.argv[2]).read()
print(tpl.replace('PROBLEM_PLACEHOLDER', sys.argv[1]))
" "$PROBLEM" "$TEMPLATE" | ollama run qwen2.5-coder:32b
