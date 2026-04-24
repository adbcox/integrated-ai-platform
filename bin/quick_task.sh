#!/bin/bash
# Quick task runner with conversation state and dual-model workflow
# Stores last 3 tasks in /tmp/task_history.json
# Supports keywords: "continue" (resume last), "fix that" (same files), "also" (extend)
# Dual-model: writer (fast) + reviewer (thorough) - enabled by default
# Usage: ./bin/quick_task.sh [--single-model] 'Task description' [file1.py file2.py ...]

set -e

# Parse flags
DUAL_MODEL=${DUAL_MODEL:-true}
EXTRA_FLAGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --single-model)
            DUAL_MODEL=false
            shift
            ;;
        --dual-model)
            DUAL_MODEL=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ $# -lt 1 ]; then
    echo "Usage: $0 [--single-model|--dual-model] 'description' [file1.py file2.py ...]"
    exit 1
fi

DESCRIPTION="$1"
shift
EXPLICIT_FILES="$@"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HISTORY_FILE="/tmp/task_history.json"
cd "$REPO_ROOT"

# Build execution flags
if [ "$DUAL_MODEL" = "true" ]; then
    EXTRA_FLAGS="--dual-model"
else
    EXTRA_FLAGS="--single-model"
fi

# Initialize history file if missing
if [ ! -f "$HISTORY_FILE" ]; then
    echo "[]" > "$HISTORY_FILE"
fi

# Helper to manage task history with Python
manage_history() {
    python3 << 'EOFPYTHON'
import json
import sys
from datetime import datetime
from pathlib import Path

history_file = "/tmp/task_history.json"

def load_history():
    try:
        with open(history_file) as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def get_last_files():
    history = load_history()
    if history:
        return history[-1].get("files", [])
    return []

def get_last_task():
    history = load_history()
    if history:
        return history[-1]
    return None

def add_task(description, files, commits):
    history = load_history()
    # Keep last 3 tasks
    history = history[-2:] if len(history) > 2 else history
    task = {
        "timestamp": datetime.utcnow().isoformat(),
        "description": description,
        "files": files,
        "commits": commits
    }
    history.append(task)
    save_history(history)

if len(sys.argv) > 1:
    cmd = sys.argv[1]
    if cmd == "get_last_files":
        files = get_last_files()
        print(" ".join(files))
    elif cmd == "add_task" and len(sys.argv) >= 5:
        description = sys.argv[2]
        files = sys.argv[3].split() if sys.argv[3] else []
        commits = sys.argv[4].split() if sys.argv[4] else []
        add_task(description, files, commits)
EOFPYTHON
}

# Determine final files based on keywords
FINAL_FILES="$EXPLICIT_FILES"
DESC_LOWER=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')

if echo "$DESC_LOWER" | grep -q "continue"; then
    LAST_FILES=$(manage_history get_last_files)
    if [ -n "$LAST_FILES" ]; then
        echo "📋 Continuing on previous files: $LAST_FILES"
        FINAL_FILES="$LAST_FILES"
    fi
elif echo "$DESC_LOWER" | grep -q "fix that"; then
    LAST_FILES=$(manage_history get_last_files)
    if [ -n "$LAST_FILES" ]; then
        echo "🔧 Re-running on same files: $LAST_FILES"
        FINAL_FILES="$LAST_FILES"
    fi
elif echo "$DESC_LOWER" | grep -q "also"; then
    LAST_FILES=$(manage_history get_last_files)
    if [ -n "$LAST_FILES" ]; then
        echo "➕ Extending context with previous files: $LAST_FILES"
        FINAL_FILES="$LAST_FILES $EXPLICIT_FILES"
    fi
fi

# Auto-commit if tree is dirty
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Staging and committing current changes..."
    git add -A
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    git commit -m "WIP: quick_task $TIMESTAMP" || true
fi

# Capture git state before task
BEFORE_SHA=$(git rev-parse HEAD)

# Run task with batch mode
echo "🚀 Running task ($EXTRA_FLAGS)..."
python3 bin/local_coding_task.py --batch-mode $EXTRA_FLAGS "$DESCRIPTION" $FINAL_FILES
TASK_EXIT=$?

# Extract modified files and commits after task
MODIFIED_FILES=""
COMMITS=""

if [ $TASK_EXIT -eq 0 ]; then
    AFTER_SHA=$(git rev-parse HEAD)

    if [ "$BEFORE_SHA" != "$AFTER_SHA" ]; then
        # Get files modified in new commits
        MODIFIED_FILES=$(git diff --name-only $BEFORE_SHA..$AFTER_SHA 2>/dev/null | tr '\n' ' ' | xargs)
        # Get new commit SHAs (short format)
        COMMITS=$(git log --format=%h $BEFORE_SHA..$AFTER_SHA 2>/dev/null | tr '\n' ' ' | xargs)
    fi

    # Save task to history
    manage_history add_task "$DESCRIPTION" "$FINAL_FILES" "$COMMITS"

    echo ""
    echo "✅ Task completed"
    [ -n "$MODIFIED_FILES" ] && echo "📝 Files modified: $MODIFIED_FILES"
    [ -n "$COMMITS" ] && echo "📌 Commits: $COMMITS"
else
    echo "❌ Task failed (exit code: $TASK_EXIT)"
    exit $TASK_EXIT
fi
