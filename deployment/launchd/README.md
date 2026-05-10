# Operator-authored launchd plists — deployment tracking

Tracks operator-personal launchd plists for the MacBook-side
inference stack (`com.adriancox.*` namespace) as version-controlled
deployment artifacts. The repo is canonical for plist content;
`~/Library/LaunchAgents/` is the deployment surface. Drift between
the two is operationally tolerated (operator may experiment locally),
but periodic reconciliation is expected — see `## Drift detection`
below.

This path is distinct from `docker/launchd-agents/` (platform
infrastructure plists under the `com.iap.*` namespace, governed by
the D-16-04.1 launchd-recency pre-commit hook). The
`launchd-recency` hook is scoped to `^docker/launchd-agents/.*\.plist$`
in `.pre-commit-config.yaml` and does NOT validate files in this
directory — operator-personal plists are tracked but not gated by
liveness checks against the platform-level launchd surface.

## Inventory

### `com.adriancox.vllm-mlx`

- **Purpose:** MLX-native vLLM fork serving `mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit` on `127.0.0.1:8500` with the `qwen3_coder` tool-call parser. Default Tier-2 stunt-double per the orchestration-layer-build migration (commit `81db99ea`).
- **Current deployment state:** ACTIVE (RunAtLoad + KeepAlive). Verified live via the integration test 2026-05-10.
- **Dependencies:**
  - Venv: `~/local-ai-workstation/venvs/vllm-mlx/` (uv-managed; raullenchai/vllm-mlx fork v0.6.30 at git `b61dec56`)
  - Model: `~/local-ai-workstation/models/mlx/qwen3-coder-30b-3bit/` (12.5 GiB, mlx-community quant, revision `322d14f29ead656431a23b827d2070baa850651f`)
  - Logs: `~/local-ai-workstation/logs/vllm-mlx.{stdout,stderr}.log`
  - Port: 8500 (LiteLLM upstream)
- **Cross-references:** `docs/orchestration-layer-build-mlx-integration-test.md` (full integration test record); CLAUDE.md §"Current Inference Stack"; KI-011 (concurrent-load validation deferred to Mac Studio).

### `com.adriancox.litellm`

- **Purpose:** LiteLLM proxy on `127.0.0.1:4000` routing model aliases (`qwen2.5-coder`, `qwen3-coder-30b-stunt-double`, `qwen3-coder-30b`) to their upstream backends per the repo-canonical config.
- **Current deployment state:** ACTIVE (RunAtLoad + KeepAlive).
- **Dependencies:**
  - Binary: `~/.local/bin/litellm` (pipx-installed)
  - Config: `~/local-ai-workstation/configs/litellm/config.yaml` (symlinked to repo `configs/litellm/config.yaml` per the migration commit; LiteLLM reads from the live path)
  - Logs: `~/local-ai-workstation/logs/litellm.{out,err}`
  - Port: 4000 (operator-facing) → 8500 (vllm-mlx upstream)
- **Cross-references:** CLAUDE.md §"Current Inference Stack"; `configs/litellm/config.yaml`.

### `com.adriancox.ollama-stunt-double`

- **Purpose:** Ollama serving on `127.0.0.1:11435` with a dedicated stunt-double-mac-studio models directory — the prior Tier-2 stunt-double, demoted by the orchestration-layer-build migration.
- **Current deployment state:** DISABLED. Live file is renamed `~/Library/LaunchAgents/com.adriancox.ollama-stunt-double.plist.disabled`. launchd ignores files without the `.plist` extension at session start. Preserved as one-step rollback if vllm-mlx issues surface before the deferred Mac Studio validations (KI-010, KI-011) close.
- **Dependencies:**
  - Binary: `/opt/homebrew/bin/ollama` (Homebrew Ollama installation)
  - Models dir: `~/local-ai-workstation/stunt-double-mac-studio/models`
  - Logs: `~/local-ai-workstation/stunt-double-mac-studio/logs/ollama.{out,err}`
  - Port: 11435 (distinct from the Tier-1 Ollama on 11434 which remains active and untouched)
- **Cross-references:** CLAUDE.md §"Current Inference Stack" (entry marks this as DEMOTED).

## Install / uninstall procedure (per plist)

Substitute `<label>` with the plist's `Label` value (e.g. `com.adriancox.vllm-mlx`).

```sh
# Install
cp deployment/launchd/<label>.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/<label>.plist

# Verify
launchctl list <label>          # PID column non-negative ⇒ running
curl -sS http://127.0.0.1:<port>/...   # service responds on declared port

# Uninstall
launchctl unload ~/Library/LaunchAgents/<label>.plist
rm ~/Library/LaunchAgents/<label>.plist

# Disable without uninstall (rollback pattern used in this session)
launchctl unload ~/Library/LaunchAgents/<label>.plist
mv ~/Library/LaunchAgents/<label>.plist ~/Library/LaunchAgents/<label>.plist.disabled
# launchd ignores files without .plist extension at session start; re-enabling
# is just the inverse rename + launchctl load.
```

## Re-provisioning runbook

If the MacBook is rebuilt or replaced, restore active plists in this
order (respect dependency edges):

1. **`com.adriancox.vllm-mlx`** — must be running before LiteLLM
   starts (LiteLLM's `qwen3-coder-30b-stunt-double` model entry
   points at `127.0.0.1:8500/v1`; LiteLLM tolerates upstream-down
   at start but service is degraded). Prerequisites:
   `~/local-ai-workstation/venvs/vllm-mlx/` recreated via uv;
   model directory populated via `hf download mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit`
   to `~/local-ai-workstation/models/mlx/qwen3-coder-30b-3bit/`.
2. **`com.adriancox.litellm`** — depends on vllm-mlx upstream on
   port 8500 and on the repo config symlink at
   `~/local-ai-workstation/configs/litellm/config.yaml` pointing at
   `configs/litellm/config.yaml` in this repo.
3. **`com.adriancox.ollama-stunt-double`** — NOT installed by
   default. Only restore if rolling back vllm-mlx (which entails
   restoring the prior LiteLLM config to route the stunt-double
   alias to `ollama_chat/qwen3-coder:30b-coding` at port 11435).
   Prerequisite: `/opt/homebrew/bin/ollama` present.

Tier-1 Ollama on `127.0.0.1:11434` is governed by Homebrew's own
service substrate, not by any plist in this directory. Out of
scope for the re-provisioning here.

## Drift detection

Compare the live plist against the repo-canonical version with the
plutil-normalized form (avoids cosmetic XML formatting differences):

```sh
for f in deployment/launchd/com.adriancox.*.plist; do
  label=$(basename "$f" .plist)
  live="$HOME/Library/LaunchAgents/$label.plist"
  if [ ! -f "$live" ]; then
    # Check for disabled state
    if [ -f "$live.disabled" ]; then
      echo "  $label: DISABLED on live surface"
      live="$live.disabled"
    else
      echo "  $label: NOT DEPLOYED"
      continue
    fi
  fi
  if diff -q <(plutil -convert xml1 -o - "$live") <(plutil -convert xml1 -o - "$f") > /dev/null; then
    echo "  $label: OK"
  else
    echo "  $label: DRIFT — review with: diff <(plutil -convert xml1 -o - $live) <(plutil -convert xml1 -o - $f)"
  fi
done
```

Surface any drift before authoring commits that modify plist content.
If the live plist is the source of an operator-side experiment that
should land in the repo, update the repo-canonical file via this
directory; if the repo is correct and the live plist drifted from a
local edit, re-install via the procedure above.

## Cross-references

- `docs/orchestration-layer-build-mlx-integration-test.md` — vllm-mlx integration test (commit `81db99ea`); §9 records the gate status, provenance disposition, and concurrent-load deferral.
- `CLAUDE.md` §"Current Inference Stack" — live state of these plists as of HEAD; intended as the session-start summary.
- `docker/launchd-agents/` — platform infrastructure plists (`com.iap.*` namespace), governed by the D-16-04.1 launchd-recency pre-commit hook. Distinct namespace from `com.adriancox.*` tracked here.
- KI-010 — upstream Qwen provenance scan deferred to Mac Studio (Mac Studio dependency shared with KI-011).
- KI-011 — concurrent-load (N=3-5) validation deferred to Mac Studio (vllm-mlx specifically).
