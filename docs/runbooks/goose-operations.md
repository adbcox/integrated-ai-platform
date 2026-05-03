# Goose operations (D-17-13)

Operator runbook for the Goose 1.x CLI execution surface paired with
Mac Studio Ollama (qwen3-coder:30b). Authored by Goose itself in
capability-validation phase; corrections applied during operator
review.

**Deployed shape (verified 2026-05-03):**

| | |
|---|---|
| Provider | `ollama` (native, direct — no litellm hop) |
| Model | `qwen3-coder:30b` |
| Host | `mac-studio.internal:11434` (Mac Studio, 192.168.10.142) |
| Ollama version | 0.22.1 |
| Context limit | 32768 (capped; native is 256K — see config comment) |
| Config (operator-local) | `~/.config/goose/config.yaml` |
| Config (repo-tracked) | `config/goose/config.yaml` |

## 1. Invocation

No launcher. Provider/model/host come from `~/.config/goose/config.yaml`
at startup.

```bash
# Interactive session (operator at the keyboard)
goose

# Headless / scripted run (smart_approve mode blocks tool approval
# without an interactive TTY; override per-invocation)
GOOSE_MODE=auto goose run --no-session --instructions /path/to/prompt.txt

# One-shot prompt (no session DB row)
GOOSE_MODE=auto goose run --no-session -t "<prompt text>"
```

The default `GOOSE_MODE=smart_approve` is correct for interactive use
(it gates tool calls behind operator approval). Headless invocations
**must** override to `auto`, otherwise the first approval-gated tool
call halts the session with `Tool approval required in non-interactive
mode`.

### Editing config

```bash
vim config/goose/config.yaml                            # repo-tracked source-of-truth
cp config/goose/config.yaml ~/.config/goose/config.yaml # apply to operator-local
goose                                                    # restart picks up changes
```

## 2. Capability posture

**Read-only substrate only.** Operator review is mandatory on all
output. Goose proposes; operator enacts.

Full posture (which extensions are enabled, which disabled, why) and
the Phase-A promotion gate live in
`docs/architecture-facts/goose-capability-boundary.md`. Do not
restate the extension list here — the chronicle is the single source
of truth.

## 3. Common failure modes

### 3.1 `mac-studio.internal` won't resolve

Symptom: `goose` reports `Could not resolve host: mac-studio.internal`,
or tool calls hang and the Goose status bar stays grey. `dig
mac-studio.internal` works correctly but `curl
http://mac-studio.internal:11434` fails.

Cause: macOS `mDNSResponder` has a cached NXDOMAIN from a query that
landed before the Dnsmasq record existed. `dscacheutil -flushcache`
does **not** clear this cache.

Fix:
```bash
sudo killall -HUP mDNSResponder
```

Verify:
```bash
python3 -c "import socket; print(socket.gethostbyname('mac-studio.internal'))"
# Expected: 192.168.10.142
```

Sub-doctrine: any time a `*.internal` Dnsmasq record is added on
OPNsense, expect to flush mDNSResponder on every macOS host that may
have queried the hostname pre-creation. See
`docs/architecture-facts/integration-audit-doctrine.md` Finding 14.

### 3.2 Ollama unreachable

Symptom: `goose` exits with `connection refused` or hangs at "goose is
ready" without progressing.

Probe:
```bash
curl -sS -m 5 http://mac-studio.internal:11434/api/tags
# Expected: JSON with {"models":[{"name":"qwen3-coder:30b",...}]}
```

If the probe fails:
- TCP-level: is Ollama running on Mac Studio? (`lsof -nP -iTCP:11434`
  on the Studio, or check `nohup`-managed PID per D-17-12 WP-05 notes)
- Bind: is Ollama bound to `0.0.0.0:11434` rather than `127.0.0.1`?
  Brew-managed Ollama defaults to localhost only; the Studio is
  currently on a `OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve`
  workaround pending the launchd plist registration in D-17-51.
- DNS: see §3.1.

### 3.3 Tool-loop hang or malformed emission

Goose's tool loop can wedge in three distinct ways. Diagnose before
remediating — restarting hides the cause.

**Malformed tool-call emission.** The model emits a
function-call-shaped token stream that doesn't parse as a valid
`tool_calls` JSON object — e.g. a stray `<functionI'll draft...`
prefix mixed into prose, or a tool name that doesn't exist in the
extension surface. Symptom: Goose prints the malformed text inline
and continues without invoking a tool. Recovery: cancel (`Ctrl+C`),
re-prompt with tighter constraints. Track recurrence in
`local-tool-calling.md` — this is qwen3-coder:30b emission noise,
not Goose's fault.

**Tool not returning.** A tool was invoked but the underlying MCP
server is hung or the network call inside it is blocked. Symptom:
`▸ tool_name extension` line appears, no response chunk follows,
session bar stays grey. Check the MCP server itself (filesystem-mcp
is `npx @modelcontextprotocol/server-filesystem`; xindex is
`python3 docker/xindex-mcp/app/server.py`). Typically a `Ctrl+C` +
restart clears it; if recurrent, restart the underlying service.

**Model context overflow.** Conversation has accumulated past the
configured `GOOSE_CONTEXT_LIMIT` (32768 currently). Symptom: cryptic
errors from the Ollama API, or model emits truncated/incoherent
output. Recovery: end the session and start a fresh one. Long-form
work that doesn't fit needs `summon`-style delegation, which is
disabled in capability-validation phase — so for now, decompose by
hand at the operator level.

### 3.4 `Tool approval required in non-interactive mode`

See §1 — set `GOOSE_MODE=auto` for headless runs. This is not a bug,
it's the smart_approve gate firing correctly when there's no TTY to
prompt on.

## 4. Operator review obligation

While capability-validation posture holds, **nothing Goose produces
lands on disk or in a commit without operator review.** The runbook
you are reading is a worked example: Goose drafted it, operator
reviewed it, frontier authored the corrected version, commit attributes
both. That is the expected pattern.

If a session produces an output that looks ship-ready, treat that as
*more* reason to read it carefully — confidence in capability-
validation phase is the failure mode.

## 5. Pointers

- `config/goose/config.yaml` — repo-tracked config
- `scripts/goose/README.md` — launcher-directory pointer doc + historical paths
- `docs/architecture-facts/goose-capability-boundary.md` — capability posture, Phase-A promotion gate
- `docs/architecture-facts/local-tool-calling.md` — substrate-side tool_calls emission findings
- `docs/architecture-facts/opnsense-dns-authority.md` + `integration-audit-doctrine.md` Finding 14 — DNS substrate + cache-invalidation sub-doctrine
