# Runbook: exo cluster operations

How to start, stop, add models to, and recover the exo distributed-
inference cluster on this platform. Consumed by operators and
future Claude sessions.

**Prerequisite read:** `docs/architecture-facts/exo-cluster.md` for
what the cluster is + what it actually does (vs what it was
designed to do — distributed inference is upstream-blocked at this
writing, see Finding O).

## Pre-flight checklist

Before any cluster operation, verify:

- Mac Mini reachable: `ssh mac-mini` (or local — operator usually
  is on the Mini directly).
- Mac Studio reachable: `ssh mac-studio` returns prompt.
- TB5 link up: `ifconfig | grep -A1 bridge` on each node shows the
  TB-Bridge interface with link-local addresses
  (`169.254.x.y/16`).
- exo venv present on each node:
  `ls ~/repos/external-tools/exo/.venv/bin/exo`.
- Models directory exists on each node:
  `mkdir -p ~/.exo/models` (Finding K — missing dir is non-fatal
  but log-noisy).
- **macOS versions aligned across nodes** (REQUIRED for any
  multi-node placement): `sw_vers` on both nodes must report the
  same `ProductVersion` AND `BuildVersion`. Empirically validated
  in D-17-25: drift on either field blocks the MlxJaccl pre-flight
  check. Single-node bring-up is unaffected by version drift.

## Cluster bring-up

**Important.** Cluster bring-up is a PROCEDURE, not a config file
(Finding Q). exo libp2p peer-id regenerates on every restart; no
CLI flag persists node identity. Each bring-up cycle:

### Step 1 — Start Mac Studio (listening peer)

On Mac Studio:

```bash
cd ~/repos/external-tools/exo
mkdir -p ~/.exo/models
nohup .venv/bin/exo \
    --libp2p-port 5678 \
    --api-port 52416 \
    -v \
    > /tmp/exo-studio.log 2>&1 &
echo "exo Studio PID: $!"
```

Do **NOT** pass `--no-downloads` (Finding P — disables
DownloadCoordinator subsystem and causes silent
DownloadModel-task rejection from the master). Provenance is
gated at the wrapper layer (`scripts/hf-download-verified.sh`),
not the runner.

### Step 2 — Capture Studio's peer-id

Wait ~5 seconds for libp2p to start, then grep the log:

```bash
STUDIO_PEER_ID=$(grep -oE '12D3KooW[A-Za-z0-9]+' /tmp/exo-studio.log | head -1)
echo "Studio peer-id: $STUDIO_PEER_ID"
```

If empty: the listening peer isn't ready yet — wait another 2-3
seconds and re-grep, or `tail -F /tmp/exo-studio.log` and look for
the first `12D3KooW…` line.

### Step 3 — Start Mac Mini (master) with bootstrap to Studio

On Mac Mini:

```bash
cd ~/repos/external-tools/exo
mkdir -p ~/.exo/models
STUDIO_PEER_ID="<paste from Step 2>"
nohup .venv/bin/exo \
    --bootstrap-peers "/ip4/169.254.35.30/tcp/5678/p2p/${STUDIO_PEER_ID}" \
    --libp2p-port 5679 \
    --api-port 52416 \
    -v \
    > /tmp/exo-mini.log 2>&1 &
echo "exo Mini PID: $!"
```

The TB-Bridge IP `169.254.35.30` is the Studio's static link-local
address (declared in the topology config). If link-locals have
changed (cable swap, new TB hardware), update accordingly.

### Step 4 — Verify cluster formed

On Mac Mini:

```bash
sleep 5
curl -s http://127.0.0.1:52416/state | python3 -m json.tool | head -30
```

Expected: `instances` may be empty (no model loaded yet); `runners`
empty; `downloads` empty or with catalog defaults. If the API
returns 404 or refuses connection, exo isn't up yet — check
`/tmp/exo-mini.log` for tracebacks.

Verify peer connectivity:

```bash
netstat -an | grep -E '169\.254\.(169\.73|35\.30):(5678|5679).*ESTABLISHED'
```

Expected: at least one ESTABLISHED line on the TB-Bridge.

## Add a model to the cluster

### Step 1 — Provenance-gated download

On Mac Mini (where the runner will load the model from cache):

```bash
cd ~/repos/integrated-ai-platform
scripts/hf-download-verified.sh mlx-community/<model-id>
```

Expect exit 3 (`verified-base-family`) for `mlx-community/*`
re-quants — this IS the canonical success state for the exo path
(Finding M; see `docs/architecture-facts/model-provenance.md`).
The wrapper proceeds on exit 0 OR 3 without override.

### Step 2 — Register and instantiate via /instance

```bash
curl -s -X POST http://127.0.0.1:52416/instance \
    -H "Content-Type: application/json" \
    -d "$(cat <<EOF
{
  "instance": $(curl -s -X POST http://127.0.0.1:52416/instance/preview \
    -H "Content-Type: application/json" \
    -d '{"modelId":"mlx-community/<model-id>"}')
}
EOF
)"
```

(In practice, fetch the preview separately and wrap as
`{"instance": <preview-MlxRingInstance-object>}`.)

The API returns a `command_id`; the master schedules placement
and the worker loads the model. Single-node placement (worldSize 1)
works today; multi-node placement currently fails with MLX
backend errors (Finding O).

### Step 3 — Verify runner ready

```bash
curl -s http://127.0.0.1:52416/state | python3 -c "
import json, sys
s = json.load(sys.stdin)
for rid, rstate in s.get('runners', {}).items():
    print(rid[:8], next(iter(rstate.keys())))
"
```

Expected: `<runner-id> RunnerReady` once load completes (typically
30-90s for a 4-bit 7B model).

### Step 4 — Smoke-test inference

```bash
curl -s -X POST http://127.0.0.1:52416/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mlx-community/<model-id>",
        "messages": [{"role":"user","content":"reply with exactly: ack"}],
        "max_tokens": 8,
        "temperature": 0.0
    }'
```

Expected: OpenAI-shaped JSON with `choices[0].message.content`
containing the response.

### Step 5 — (Optional) Add to litellm-gateway as a route

For platform-wide consumption via the litellm Bearer-auth surface,
add a route to `~/control-center-stack/stacks/gateways/
litellm_config.yaml`:

```yaml
  - model_name: exo-<short-name>
    litellm_params:
      model: openai/mlx-community/<model-id>
      api_base: http://host.docker.internal:52416/v1
      api_key: "sk-no-key-required"  # pragma: allowlist secret
```

Then `docker restart litellm-gateway` and verify with
`curl -H "Authorization: Bearer $LITELLM_MASTER_KEY"
http://127.0.0.1:4000/v1/models | grep exo-<short-name>`.

The literal `api_key` is a placeholder satisfying litellm's
openai-provider client schema. NOT a credential.

## Cluster shutdown

Canonical kill pattern (Finding R — DO NOT use cmdline-flag-
substring matching, which misses one or both nodes due to
asymmetric cmdlines):

On each node:

```bash
pkill -f '\.venv/bin/exo' || true
```

Or, if you saved PIDs at bring-up time, kill by PID directly.

Verify:

```bash
pgrep -lf exo  # should return nothing on either node
```

## Recovery procedures

### Cluster doesn't form (no ESTABLISHED on TB-Bridge)

- Check that both `--libp2p-port`s match the bootstrap-peers
  multiaddr (Mini bootstraps to Studio's port 5678; Studio listens
  on 5678).
- Check the peer-id in Mini's bootstrap-peers matches Studio's
  CURRENT peer-id (not a stale one from a previous session —
  Finding Q).
- Check TB-Bridge interface up:
  `ifconfig | grep -A2 bridge` on each node.
- Restart in correct order: Studio first, capture peer-id, then
  Mini.

### Runner stays in DownloadModel loop

Symptom: `/state` shows `downloads` advancing on a node, but
runner never reaches `RunnerReady`.

- Confirm the worker was NOT started with `--no-downloads`
  (Finding P). If it was, restart that node without the flag.
- Confirm disk space on `~/.exo/models` (df -h ~).
- Check the worker's log for tracebacks: `tail -F /tmp/exo-<node>.log`.

### Inference returns 503 / model not found

- `/v1/models` lists exo's full catalog (~120 entries) regardless
  of what's loaded. The relevant question is `/state`:
  `runners[*].RunnerReady` for your model's runner.
- If runner is `RunnerIdle` or missing: the instance was created
  but placement failed. Check the master log for placement errors.

### Multi-node placement fails

Expected as of D-17-25 close (Outcome C). Distributed inference
remains upstream-blocked. Failure modes seen in practice:

- **MlxRing 2-node placement** → planner rejects with
  `MLX ring backend requires connectivity between neighbouring
  nodes`. Same error class as D-17-14; macOS alignment did not
  change this for the ring backend.
- **MlxJaccl 2-node placement** (post-macOS-alignment, D-17-25):
  planner accepts, valid Instance object returned, POST `/instance`
  returns 200 with `command_id`, runner subprocesses start on both
  nodes and enter `mlx_distributed_init`, then SIGSEGV with
  `Runner terminated with signal=11 (Segmentation fault: 11)`
  inside MLX/jaccl C++. Cause is two interacting upstream gaps:
  - **Finding U** — `MLX_JACCL_COORDINATOR` selects a LAN address
    (`192.168.10.142:52617`) instead of the libp2p static-peer
    TB-Bridge multiaddr. Matches upstream `MISSED_THINGS.md`
    (`get_mlx_jaccl_coordinators picks the first one, which is
    unstable`).
  - **Finding V** — runner's `MLX_IBV_DEVICES` matrix is populated
    even when `nodeRdmaCtl.enabled=false`, with no graceful
    fallback to TCP; runner crashes when it tries to use
    uninitialized RDMA devices.

Single-node placement (`worldSize: 1` to one peer-id) still works.
For multi-node, watch for an upstream exo release that covers
BOTH Finding U (coordinator IP selection) and Finding V (RDMA
control-plane / runner gating). Reproducer evidence preserved at
`docs/phase-17/d-17-25-wp-05-multinode-evidence/`.

## Health checks

### Quick liveness

```bash
curl -fs http://127.0.0.1:52416/state > /dev/null && echo "Mini exo: up" || echo "Mini exo: down"
ssh mac-studio 'curl -fs http://127.0.0.1:52416/state > /dev/null && echo "Studio exo: up" || echo "Studio exo: down"' 2>/dev/null
```

### Cluster pairing

```bash
netstat -an 2>/dev/null | grep -E '169\.254\.(169\.73|35\.30):(5678|5679).*ESTABLISHED' | wc -l
```

Expected: ≥1.

### Runner state

```bash
curl -s http://127.0.0.1:52416/state | python3 -c "
import json, sys
s = json.load(sys.stdin)
runners = s.get('runners', {})
print(f'runners: {len(runners)}')
for rid, rstate in runners.items():
    print(f'  {rid[:8]}: {next(iter(rstate.keys()))}')
"
```

## See also

- `docs/architecture-facts/exo-cluster.md` — what the cluster is +
  partial-completion framing
- `docs/architecture-facts/model-provenance.md` — D-17-10 gate
  semantics (exit 0 vs exit 3)
- `docs/runbooks/pull-new-model.md` — model-pull procedure
  including override mechanism (rare for exo path)
- `~/repos/external-tools/exo/MISSED_THINGS.md` — upstream's own
  list of known gaps
