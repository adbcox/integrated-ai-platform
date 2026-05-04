#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
git_dir="$(git -C "$repo_root" rev-parse --git-dir)"
hook_path="$git_dir/hooks/post-commit"

cat > "$hook_path" <<'HOOK'
#!/usr/bin/env bash
set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
git_dir="$(git rev-parse --git-dir 2>/dev/null || echo .git)"
log_file="$git_dir/push.log"

# Skip auto-push when merge or rebase workflow is in progress.
if [ -f "$git_dir/MERGE_HEAD" ] || [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; then
  {
    printf '%s [%s] skip: merge/rebase in progress\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "post-commit"
  } >> "$log_file"
  exit 0
fi

{
  printf '%s [%s] enqueue: git push origin main\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "post-commit"
} >> "$log_file"

nohup env REPO_ROOT="$repo_root" LOG_FILE="$log_file" bash -c '
  cd "$REPO_ROOT" >/dev/null 2>&1 || exit 0
  ts="$(date -u +'\''%Y-%m-%dT%H:%M:%SZ'\'')"
  if out="$(GIT_TERMINAL_PROMPT=0 git push origin main 2>&1)"; then
    {
      printf "%s [%s] success: git push origin main\n" "$ts" "post-commit"
      printf "%s\n" "$out"
    } >> "$LOG_FILE"
  else
    rc=$?
    {
      printf "%s [%s] fail-soft rc=%s: git push origin main\n" "$ts" "post-commit" "$rc"
      printf "%s\n" "$out"
    } >> "$LOG_FILE"
  fi
' >/dev/null 2>&1 &

exit 0
HOOK

chmod +x "$hook_path"
echo "Installed $hook_path"
echo "Audit log: $git_dir/push.log"
