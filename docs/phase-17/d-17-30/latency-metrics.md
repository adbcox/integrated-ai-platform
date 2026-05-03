# D-17-30 — Latency metrics + smoke evidence

**Date:** 2026-05-03
**Scope:** Single-node exo on Mac Mini M4 Pro 48 GB · model `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` (4.28 GB on disk)
**Cluster:** 1 node (peer-id `12D3KooWAUqbiNsXfU2mu4x2FDVfywp49ts7Lmq7YWuFt9JXoy58`), 1 runner, MlxRing instance, 28 layers, single shard
**Process:** PID file `/tmp/exo-mini-d17-30.pid`, log `/tmp/exo-mini-d17-30.log`
**API:** `http://127.0.0.1:52416` (libp2p `5679`)

## Path verified

```
Open WebUI (open-webui:3002 host / 172.23.0.22 internal)
  → litellm-gateway:4000 (model alias: exo-qwen-coder-7b)
    → host.docker.internal:52416/v1 (exo OpenAI-compat surface)
      → MlxRing runner 469f98f3 (state: RunnerReady)
        → MLX inference on Apple Silicon (M4 Pro)
```

## Direct exo (non-streamed, short prompt)

| Metric        | Value     |
| ------------- | --------- |
| Wall time     | 1.39 s    |
| Prompt tokens | 52        |
| Completion    | 59 tokens |
| Effective     | ~42 tok/s |

Prompt: "Write a Python function that returns the nth Fibonacci number using memoization."
Output: correct memoized recursive implementation.

## Direct exo (streamed, longer prompt)

| Metric                   | Value      |
| ------------------------ | ---------- |
| TTFT                     | **0.404 s** |
| Total wall               | 2.786 s    |
| Generation phase         | 2.382 s    |
| SSE chunks (≈tokens)     | 130        |
| Sustained throughput     | **54.6 tok/s** |

Prompt: "Write a Python function to compute the SHA-256 hash of a file in 64KB chunks. Include a brief docstring."
Output: idiomatic `hashlib.sha256` walrus-loop implementation with docstring.

## Through litellm (host)

| Metric    | Value  |
| --------- | ------ |
| Wall time | 0.64 s |
| Output    | "The capital of France is Paris." |

## Through Open WebUI's network (container → litellm → exo)

| Metric    | Value  |
| --------- | ------ |
| Wall time | 0.42 s |
| Output    | "PARIS" |

Full chain confirmed end-to-end from inside `open-webui` container's network namespace using its actual runtime credentials (sourced from PID 1 `/proc/1/environ` per Finding DD).

## Model visibility from Open WebUI's perspective

`/v1/models` request from inside `open-webui` container returns 6 routes; `exo-qwen-coder-7b` is one of them — confirms OWU's model picker will list and route to exo.

## Screenshots

- `open-webui-auth.png` — OWU login splash on host port 3002 (service reachable, SPA hydrating). Inside-app model-picker capture deferred (would need authenticated session cookie; non-blocking for demo since the API-level proof above is stronger evidence than a screenshot of a dropdown).
- `open-webui-models.png` — initial loading frame.

## Notes

- Single-node placement uses `MlxRing` instance / `Pipeline` sharding — same API surface as multi-node, so litellm config will not change when distributed inference unblocks (Findings U+V).
- Runner "state" in `/state` payload is encoded as `{"RunnerReady": {}}` (Rust enum tag) rather than a `state` field. Worth a runbook note for future state-polling code.
- `docker exec ... sh -c 'echo $VAR'` shows empty for `OPENAI_API_KEY` because it's loaded by entrypoint into PID 1 only (Finding DD); use `tr "\0" "\n" < /proc/1/environ | grep ^VAR=` for diagnostic reads.
