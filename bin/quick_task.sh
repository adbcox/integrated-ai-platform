#!/bin/bash
# Quick task runner - auto-commits and executes without checks
# Usage: ./bin/quick_task.sh 'Task description' file1.py [file2.py ...]

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 'description' file1.py [file2.py ...]"
    exit 1
fi

DESCRIPTION="$1"
shift
FILES="$@"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Auto-commit if tree is dirty
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Staging and committing current changes..."
    git add -A
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    git commit -m "WIP: quick_task $TIMESTAMP" || true
fi

# Run task with batch mode (force, skip analysis)
echo "🚀 Running task..."
python3 bin/local_coding_task.py --batch-mode "$DESCRIPTION" $FILES
