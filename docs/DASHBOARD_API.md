# Dashboard API Reference

The AI Platform dashboard server (`web/dashboard/server.py`) exposes a JSON API.

**Base URL:** `http://localhost:8080` (or `http://mac-mini.local:8080`)

All responses are JSON. All GET endpoints support CORS (`Access-Control-Allow-Origin: *`).
HTML responses allow iframe embedding (`Content-Security-Policy: frame-ancestors *`).

---

## Health & Status

### `GET /api/health`
Lightweight health check. Used by Docker HEALTHCHECK and load balancers.

```json
{
  "status": "ok",
  "service": "ai-platform-dashboard",
  "version": "1.0.0",
  "ts": 1714000000.0,
  "repo_root": "/app",
  "executor_host": "mac-studio.local"
}
```

### `GET /api/embed/widget`
Compact stats for Homepage/Homarr widget integration. Fast — no git log or training stats.

```json
{
  "completions":      42,
  "accepted":         8,
  "in_progress":      3,
  "pending":          127,
  "total":            180,
  "success_rate":     28,
  "executor_running": true,
  "current_item":     "RM-FLOW-001",
  "ollama_available": true,
  "cpu_pct":          45.2,
  "ram_used_pct":     62
}
```

### `GET /api/status`
Full platform status. Heavier — aggregates roadmap, execution, git, training, system.

```json
{
  "ts": 1714000000.0,
  "roadmap": {
    "total": 180, "completed": 42, "accepted": 8,
    "in_progress": 3, "pending": 127
  },
  "execution": {
    "log_file": "/tmp/executor_longrun.log",
    "is_running": true,
    "current_item": "RM-FLOW-001",
    "current_subtask": "Add guard clause to auto_execute_roadmap.py",
    "subtask_index": 2,
    "subtask_total": 5,
    "elapsed_seconds": 143,
    "live_status": "Running aider",
    "completion_count": 42,
    "failure_count": 3,
    "avg_subtask_seconds": 47.2,
    "subtask_history": [45.1, 52.3, ...]
  },
  "git": [
    {"hash": "1a4b810", "message": "status: RM-APIGW-001 → Accepted",
     "when": "2 hours ago", "author": "Adrian Cox", "files": [...]}
  ],
  "training": {
    "quality_examples": 156, "sft_ready": true, "lora_ready": true,
    "sft_threshold": 5, "lora_threshold": 50, "stable_threshold": 200
  },
  "system": {
    "ollama_available": true, "ollama_queue": 1,
    "aider_processes": 1, "executor_running": true,
    "disk_free_gb": 120, "cpu_pct": 45.2,
    "ram_used_pct": 62, "ram_total_gb": 32
  },
  "categories": [
    {"category": "SCALE", "total": 10, "done": 3, "pct": 30},
    ...
  ]
}
```

---

## Roadmap

### `GET /api/kanban`
Items grouped by status for the Kanban board view.

```json
{
  "In progress": [{"id": "RM-FLOW-001", "title": "Auto-merge PRs", "category": "FLOW"}],
  "Pending":     [...],
  "Completed":   [...],
  "Accepted":    [...]
}
```

### `GET /api/recommendations`
Top 5 next quick-win items (no pending dependencies, ranked by easiness).

```json
{
  "items": [
    {
      "id": "RM-FLOW-001", "title": "Auto-merge for passing PRs",
      "category": "FLOW", "loe": "S", "risk": 2,
      "easiness": 85.0, "unlocks": 3, "filter": "RM-FLOW-001"
    }
  ]
}
```

---

## Executor Control

### `GET /api/executor/status`
Lightweight polling endpoint (designed for 2-second intervals).

```json
{
  "running":             true,
  "current_item":        "RM-FLOW-001",
  "current_subtask":     "Writing test assertions",
  "subtask_index":       3,
  "subtask_total":       5,
  "elapsed_seconds":     210,
  "live_status":         "Running aider",
  "avg_subtask_seconds": 47.2,
  "completion_count":    42,
  "failure_count":       3
}
```

### `POST /api/executor`
Start or stop the executor.

**Start:**
```json
{"action": "start", "max_items": 50, "filter": "RM-FLOW-"}
```
```json
{"ok": true, "message": "Started PID 12345", "pid": 12345, "log": "/tmp/executor_longrun.log"}
```

**Stop:**
```json
{"action": "stop"}
```
```json
{"ok": true, "message": "Stopped PID(s) 12345"}
```

When `EXECUTOR_HOST` is set, these actions SSH to the remote host instead of running locally.

---

## Logs

### `GET /api/log`
Last 200 lines from the most recently modified executor log.

```json
{
  "lines": ["2026-04-24 10:00:00 🚀 Starting RM-FLOW-001", ...],
  "file": "/tmp/executor_longrun.log"
}
```

### `GET /api/diff/{hash}`
Git diff for a specific commit hash (7–40 hex chars).

```json
{
  "hash": "1a4b810",
  "stat": " bin/auto_execute_roadmap.py | 5 +++--\n ...",
  "diff": "diff --git a/bin/auto_execute_roadmap.py ..."
}
```

---

## Training

### `GET /api/training/status`
Training cycle progress.

```json
{
  "is_running":       true,
  "done":             false,
  "step":             150,
  "total_steps":      500,
  "progress_percent": 30,
  "current_step":     "Training LoRA adapter",
  "eta_minutes":      12,
  "log_tail":         ["Step 150/500  loss=0.423 ...", ...],
  "log_file":         "/tmp/training_cycle.log"
}
```

### `POST /api/training/start`
Launch a training cycle.

```json
{"ok": true, "message": "Training started (PID 23456)", "estimated_minutes": 45}
```

### `POST /api/model/deploy`
Load the trained LoRA adapter into Ollama as `qwen2.5-coder:custom`.

```json
{"ok": true, "message": "qwen2.5-coder:custom deployed to Ollama"}
```

---

## Environment Variables

Configure the server via environment variables (key for Docker deployments):

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_ROOT` | computed from `__file__` | Path to the repository root |
| `ITEMS_DIR` | `REPO_ROOT/docs/roadmap/ITEMS` | Roadmap items directory |
| `LOG_DIR` | `/tmp` | Directory for executor/training logs |
| `EXECUTOR_HOST` | _(empty)_ | SSH host for remote executor control |
| `REMOTE_REPO_ROOT` | `~/repos/integrated-ai-platform` | Repo path on EXECUTOR_HOST |
| `OLLAMA_HOST` | `127.0.0.1:11434` | Ollama API host:port |

---

## Integration Examples

### Homepage custom API widget
```yaml
widget:
  type: customapi
  url: http://ai-platform-dashboard:8080/api/embed/widget
  method: GET
  mappings:
    - field: completions
      label: Done
      format: number
    - field: success_rate
      label: Rate
      format: percent
```

### curl health check
```bash
curl -sf http://localhost:8080/api/health | python3 -m json.tool
```

### Iframe embed
```html
<iframe src="http://mac-mini.local:8080" width="100%" height="600"
        style="border:none;border-radius:10px"></iframe>
```
Works because the dashboard sets `Content-Security-Policy: frame-ancestors *`.

### JavaScript polling
```javascript
const poller = ApiPoller({
  url: '/api/executor/status',
  intervalMs: 2000,
  onData: (data) => updateUI(data),
  onError: (err) => console.warn('Poll failed:', err),
});
poller.start();
```
(Uses `ApiPoller` from `web/shared/components.js`)
