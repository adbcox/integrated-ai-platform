# D-17-12 WP-03 — Model acquisition + verification

**Date:** 2026-05-03

## Outcome

All four models present and addressable:

| Tier | Model | Host | Daemon | Size on disk | Quant | Context limit | Family |
|---|---|---|---|---|---|---|---|
| T1 | `qwen2.5-coder:32b` | Mac Mini (.145) | :11434 (`ollama serve`) | 19 GB | Q4_K_M | 32768 | qwen2 |
| T2 | `qwen2.5-coder:14b` | Mac Mini (.145) | :11434 (`ollama serve`) | 9 GB | Q4_K_M | 32768 | qwen2 |
| T3-A | `gemma2:27b` | Mac Studio (.142) | :11434 (`brew services`) | 15 GB | Q4_0 | **8192** | gemma2 |
| T3-B | `qwen3-coder:30b` | Mac Studio (.142) | :11434 (`brew services`) | 18 GB | Q4_K_M | **262144** | qwen3moe |

## Daemon state

| Host | Ollama version | Start mechanism | Persistence |
|---|---|---|---|
| Mac Mini | 0.20.7 | `nohup ollama serve` foreground (PID 91086) | Until next reboot — `brew services start ollama` failed with launchctl error 125 ("Domain does not support specified action"), which is exactly D-17-25 Finding Y (launchctl user-domain registry disrupted by 2026-05-02 macOS upgrade, never re-registered) |
| Mac Studio | 0.22.1 | `brew services start ollama` succeeded | Persistent (launchd-managed) |

**Version drift caveat for benchmark fairness:** Mini at 0.20.7,
Studio at 0.22.1. Ollama 0.21+ added MoE-specific scheduler
optimizations and changed the default flash-attention behavior.
The benchmark report must record this as a confound — observed
T3 wins on Studio could partially attribute to the newer Ollama,
not just the model + hardware. Upgrading Mini's Ollama is a
separate deliverable (not part of D-17-12 hard cap); flagging the
asymmetry is what we can do here.

**Mini daemon mechanism caveat:** the foreground `ollama serve`
will die on Mac Mini reboot. For benchmark continuity within
D-17-12 this is fine (WP-05 runs in one sitting). For the broader
"future-reuse asset" framing this needs Finding Y resolution
(re-register launchctl user-domain agents) — added to Phase 17
follow-up backlog.

**Follow-on resolved (D-17-58, 2026-05-03):** Mac Studio Ollama
persistence is now codified via a LaunchDaemon install path
(`docker/launchd-agents/com.iap.ollama.plist` +
`scripts/install-ollama-launchdaemon-mac-studio.sh`) under the
D-17-51 system-domain doctrine (`UserName=admin`, `/Library/LaunchDaemons`).
This replaces nohup-era continuity assumptions for the Mac Studio
execution-role substrate.

## Critical fairness finding — context-window asymmetry

| Model | Context | Suitable for 16K+ workload? |
|---|---|---|
| qwen2.5-coder:32b | 32K | YES |
| qwen2.5-coder:14b | 32K | YES |
| gemma2:27b | **8K** | **NO — would silently truncate** |
| qwen3-coder:30b | 256K | YES (native long-context model) |

Gemma 2 is fundamentally not a long-context model; its 8K window
is a decided architectural property. Pushing 16K+ inputs to
gemma2:27b would be measuring "how does Ollama handle truncation"
not "how does Gemma 2 reason over long contexts."

**Harness implication for WP-04:** the long-context workload runs
the THREE long-context-capable models (T1, T2, T3-B) at 16K input
size, and runs Gemma at 7K input size with a clear annotation that
the result is "best-effort 7K performance" not a comparable long-
context number. This honors the "specialty workload" framing
(Gemma's specialty is general reasoning at conventional context,
not long-context).

This finding strengthens Qwen3-Coder's specialty thesis: 256K
native window is a different class than 32K. If Qwen3-Coder
wins on 16K, the natural next question is whether it stays
useful at 64K / 128K / 256K — but that's beyond D-17-12 scope.

## Quant-class asymmetry

- gemma2:27b ships at Q4_0 (older, simpler quant scheme)
- qwen2.5-coder:* and qwen3-coder:30b ship at Q4_K_M (newer,
  better quality preservation per bit)

Q4_0 is generally 1–3% lower quality than Q4_K_M at the same
parameter count. Recording so the report doesn't hand-wave a
gemma2-vs-qwen quality gap as purely model-architectural.

The right way to disambiguate would be to also run gemma2:27b at
a Q4_K_M re-quantization — but Ollama's published gemma2:27b is
Q4_0, and re-quantizing locally is out of scope for D-17-12. Note
the limitation in the chronicle.

## Storage footprint

Total weights pulled this WP: 33 GB (15 + 18 on Mac Studio).
Mac Mini weights pre-existing (29 GB across baseline models, no
new pulls).

## Tag-resolution note

`Qwen/Qwen3-Coder-30B-A3B-Instruct` (HF repo path used in WP-02
provenance scan) maps to Ollama tag `qwen3-coder:30b` — Ollama's
default tag for the Qwen3-Coder family at 30B. The `30b-a3b`,
`30b-a3b-instruct`, and `qwen3-coder-30b-a3b` variants all return
HTTP 404 against the registry; the canonical Ollama tag is just
`qwen3-coder:30b`. Recorded so future operators don't waste time
hunting for a more-specific tag that doesn't exist on Ollama's
side.
