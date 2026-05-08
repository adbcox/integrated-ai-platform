#!/usr/bin/env bash
set -euo pipefail

# Get all local branches sorted alphabetically
branches=$(git branch --format='%(refname:short)' | sort)

# Process main first if it exists
if echo "$branches" | grep -q "^main$"; then
  echo "── main ──"
  tip_hash=$(git rev-parse --short main)
  tip_subject=$(git log -1 --format=%s main)
  echo "$tip_hash $tip_subject"
  echo
fi

# Process other branches in alphabetical order
echo "$branches" | while IFS= read -r branch; do
  [ "$branch" = "main" ] && continue
  [ -z "$branch" ] && continue

  echo "── $branch ──"
  tip_hash=$(git rev-parse --short "$branch")
  tip_subject=$(git log -1 --format=%s "$branch")
  echo "$tip_hash $tip_subject"

  # Get commits ahead of main
  ahead_count=$(git rev-list --count main.."$branch" || echo 0)
  if [ "$ahead_count" -gt 0 ]; then
    echo "$ahead_count commits ahead of main"
    # List commits oldest first (reverse order)
    git rev-list --pretty=format:"%h %s" main.."$branch" \
      | grep -v "^commit" \
      | awk '{ lines[NR]=$0 } END { for(i=NR; i>=1; i--) print "  " lines[i] }'
  fi

  echo
done

# Print working tree status
git status -sb | head -1
