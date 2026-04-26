# Integrated AI Platform — Systems Guide

This guide covers all 26 production systems in the Integrated AI Platform. Systems are organized
into five categories: **Framework** (5 cross-cutting infrastructure systems), **Media Intelligence**
(5 domain systems), **Roadmap Analytics** (5 domain systems), **Execution Engine** (5 domain
systems), and **Training** (4 domain systems). The canonical source of truth for module paths,
config keys, and event names is `config/systems.yaml`.

---

## Table of Contents

1. [API Quick Reference](#api-quick-reference)
2. [Framework Systems](#framework-systems)
3. [Media Intelligence Systems](#media-intelligence-systems)
4. [Roadmap Analytics Systems](#roadmap-analytics-systems)
5. [Execution Engine Systems](#execution-engine-systems)
6. [Training Systems](#training-systems)
7. [Event Bus Conventions](#event-bus-conventions)
8. [Metrics Convention](#metrics-convention)
9. [Configuration](#configuration)

---

## API Quick Reference

Nine systems expose HTTP endpoints. All return JSON unless noted.

| Method | Path                          | System               | Description                                      | Response shape (top-level keys)                         |
|--------|-------------------------------|----------------------|--------------------------------------------------|---------------------------------------------------------|
| GET    | `/api/metrics`                | metrics_system       | Prometheus-compatible metrics snapshot           | `counters`, `gauges`, `histograms`, `timestamp`         |
| GET    | `/api/media/quality-scores`   | quality_analyzer     | Quality scores for media library items           | `items[]` → `{id, resolution_score, hdr_score, codec_score, audio_score, composite}` |
| GET    | `/api/media/bandwidth`        | bandwidth_manager    | Current network utilisation + throttle state     | `bytes_sent`, `bytes_recv`, `throttled`, `limit_mbps`   |
| GET    | `/api/media/recommendations-ai` | content_recommender | AI-embedding recommendations for a given item   | `item_id`, `recommendations[]` → `{id, title, score, method}` |
| GET    | `/api/analytics/dependencies` | dependency_analyzer  | Roadmap item dependency graph (D3-ready)         | `nodes[]`, `edges[]`, `cycles[]`, `generated_at`        |
| GET    | `/api/analytics/effort`       | effort_predictor     | LOE estimates + Monte Carlo sprint forecast      | `items[]` → `{id, loe, p80_days, p95_days}`, `forecast` |
| GET    | `/api/analytics/priorities`   | priority_engine      | Ranked roadmap items with priority scores        | `items[]` → `{id, score, quick_win, bottleneck}`, `ranked_at` |
| GET    | `/api/analytics/progress`     | progress_analytics   | Velocity, burndown series, forecast completion   | `velocity`, `burndown[]`, `burnup[]`, `forecast_date`   |
| GET    | `/api/training/viz`           | training_viz         | Live training metrics for dashboard consumption  | `epochs[]` → `{loss, val_loss, f1, lr}`, `overfitting`  |

All endpoints accept an optional `?format=prometheus` query parameter on `/api/metrics` to switch
to Prometheus text format.

---

## Framework Systems

Framework systems provide cross-cutting infrastructure used by every domain system. They do not
implement business logic; they provide primitives that domain systems build on.

---

### event_system

**Module**: `framework.event_system`

Pub/sub event bus with fnmatch wildcard pattern subscriptions, a dead-letter queue (DLQ) for
failed deliveries, and JSONL persistence so events survive process restarts.

**Key classes / functions**

| Name | Role |
|------|------|
| `EventBus` | Central singleton; `publish()`, `subscribe()`, `unsubscribe()` |
| `Event` | Dataclass: `name`, `payload`, `timestamp`, `source` |
| `DeadLetterQueue` | Holds undeliverable events; max size `dlq_max_size` (default 1000) |
| `PersistentEventLog` | Appends every event to `artifacts/events.jsonl` |

**Usage example**

```python
from framework.event_system import EventBus, Event

bus = EventBus()

# Subscribe with a wildcard — receives any event whose name matches the pattern
def on_media_event(event: Event) -> None:
    print(f"Received {event.name}: {event.payload}")

bus.subscribe("media.*.*", on_media_event)

# Publish from any system
bus.publish(Event(
    name="media.quality.scored",
    payload={"item_id": "tt1234567", "composite": 0.87},
    source="quality_analyzer",
))
```

**Config keys** (`config/systems.yaml → framework.event_system.config`)

| Key | Default | Notes |
|-----|---------|-------|
| `dlq_max_size` | 1000 | Events beyond this are dropped with a warning |
| `persistence_path` | `artifacts/events.jsonl` | Set to `null` to disable persistence |
| `thread_pool_workers` | 4 | Parallel subscriber dispatch workers |

---

### connector_framework

**Module**: `framework.connector_framework`

`BaseConnector` abstract base class providing a circuit breaker, connection pool, and a
central registry so systems can look up connectors by name rather than instantiating them
directly.

**Key classes / functions**

| Name | Role |
|------|------|
| `BaseConnector` | ABC; subclass and implement `_connect()`, `_disconnect()`, `_health_check()` |
| `CircuitBreaker` | Tracks failures; opens after `circuit_breaker_failures` (default 5) consecutive failures |
| `ConnectionPool` | Maintains up to `pool_max_size` (default 10) live connections |
| `ConnectorRegistry` | `register(name, connector)` / `get(name)` global lookup |

**Usage example**

```python
from framework.connector_framework import BaseConnector, ConnectorRegistry

class SonarrConnector(BaseConnector):
    def _connect(self):
        # establish HTTP session to Sonarr API
        ...

    def _health_check(self) -> bool:
        return self.session.get("/api/v3/system/status").ok

connector = SonarrConnector(base_url="http://sonarr:8989", api_key="...")
ConnectorRegistry.register("sonarr", connector)

# Later, in any domain system:
sonarr = ConnectorRegistry.get("sonarr")
```

**Config keys**

| Key | Default | Notes |
|-----|---------|-------|
| `circuit_breaker_failures` | 5 | Consecutive failures before opening |
| `circuit_breaker_timeout` | 30 s | How long the circuit stays open |
| `pool_max_size` | 10 | Max live connections per connector |
| `half_open_test_interval` | 60 s | How often to probe a half-open circuit |

---

### config_system

**Module**: `framework.config_system`

YAML-based configuration loader with deep-merge semantics (environment files overlay base
config), `ENC[...]` Fernet-encrypted value support, and file-system watch-based hot reload.

**Key classes / functions**

| Name | Role |
|------|------|
| `ConfigLoader` | `load(path)` returns merged dict; `watch()` starts hot-reload thread |
| `ConfigEncryption` | `decrypt(value)` unwraps `ENC[base64...]` tokens using `CONFIG_ENCRYPTION_KEY` env var |
| `deep_merge(base, overlay)` | Recursively merges two dicts; overlay wins on scalar conflicts |

**Usage example**

```python
from framework.config_system import ConfigLoader

loader = ConfigLoader(config_dir="config/")
cfg = loader.load("systems.yaml")

# Access a nested key safely
limit = cfg["media_intelligence"]["bandwidth_manager"]["config"]["throttle_limit_mbps"]

# Start hot reload — callback fires on any change
loader.watch(callback=lambda new_cfg: print("Config reloaded"))
```

**Encrypting a secret**

```bash
python3 -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
print('Key:', key.decode())
print('Encrypted:', f'ENC[{f.encrypt(b\"my-secret\").decode()}]')
"
# Set CONFIG_ENCRYPTION_KEY=<key> in your environment
```

---

### metrics_system

**Module**: `framework.metrics_system`

Lightweight Counter / Gauge / Histogram metric primitives with in-process time-series storage
and a Prometheus-compatible `/api/metrics` export endpoint.

**Key classes / functions**

| Name | Role |
|------|------|
| `MetricsRegistry` | Singleton; `counter(name)`, `gauge(name)`, `histogram(name)` factories |
| `Counter` | Monotonically increasing; `increment(n=1)` |
| `Gauge` | Settable current value; `set(v)`, `increment(n)`, `decrement(n)` |
| `Histogram` | Bucketed; `observe(value)` |
| `PrometheusExporter` | Serialises registry to Prometheus text format |

**Usage example**

```python
from framework.metrics_system import MetricsRegistry

reg = MetricsRegistry()
tasks_total = reg.counter("iap_tasks_total")
queue_depth = reg.gauge("iap_queue_depth")
latency_ms  = reg.histogram("iap_task_latency_ms")

tasks_total.increment()
queue_depth.set(42)
latency_ms.observe(312.5)

# Export for Prometheus scrape
print(reg.export_prometheus())
```

**Config keys**

| Key | Default | Notes |
|-----|---------|-------|
| `time_series_maxlen` | 10000 | Rolling window per metric |
| `prometheus_prefix` | `iap_` | Prepended to all exported metric names |
| `scrape_interval` | 15 s | Advisory; actual scrape is driven by Prometheus |

---

### monitoring_system

**Module**: `framework.monitoring_system`

Distributed tracing (Span / trace context propagation via `threading.local`), a `@trace()`
decorator for automatic span creation, and `AlertRule` evaluation against live metric values.

**Key classes / functions**

| Name | Role |
|------|------|
| `Tracer` | `start_span(name)` context manager; propagates trace-id via `threading.local` |
| `Span` | `name`, `trace_id`, `parent_id`, `start_time`, `end_time`, `tags` |
| `trace(name)` | Decorator; wraps a function in a span automatically |
| `AlertRule` | `condition` callable over metrics; `fire()` calls registered handlers |
| `AlertManager` | Evaluates all rules every `alert_eval_interval` seconds |

**Usage example**

```python
from framework.monitoring_system import Tracer, trace

tracer = Tracer()

# Manual span
with tracer.start_span("rag4.rerank") as span:
    span.tags["query"] = "improve ExecutorFactory"
    result = run_rerank(query)

# Decorator
@trace("quality_analyzer.score")
def score_item(item_id: str) -> dict:
    ...
```

**Defining an alert rule**

```python
from framework.monitoring_system import AlertRule, AlertManager
from framework.metrics_system import MetricsRegistry

reg = MetricsRegistry()
manager = AlertManager(metrics_registry=reg, eval_interval=30)

manager.add_rule(AlertRule(
    name="high_queue_depth",
    condition=lambda metrics: metrics["iap_queue_depth"].value > 500,
    handler=lambda rule: print(f"ALERT: {rule.name}"),
))
manager.start()
```

---

## Media Intelligence Systems

These five systems provide intelligence for automated media management (Sonarr / Radarr /
Prowlarr stack integration).

---

### quality_analyzer

**Module**: `domains.quality_analyzer`

Scores individual media releases across four dimensions (resolution, HDR, codec, audio) and
generates Sonarr/Radarr quality-profile recommendations from those scores.

**Key classes / functions**

| Name | Role |
|------|------|
| `QualityAnalyzer` | `score(release: dict) -> QualityScore`; `recommend_profile(scores) -> dict` |
| `QualityScore` | Dataclass: `resolution`, `hdr`, `codec`, `audio`, `composite` (weighted sum) |
| `ProfileGenerator` | Maps composite score ranges to Sonarr/Radarr profile names |

**Scoring weights** (from `config/systems.yaml`)

| Dimension | Weight |
|-----------|--------|
| Resolution | 0.30 |
| HDR | 0.25 |
| Codec | 0.25 |
| Audio | 0.20 |

**Usage example**

```python
from domains.quality_analyzer import QualityAnalyzer

qa = QualityAnalyzer()
score = qa.score({
    "resolution": "2160p",
    "hdr": "HDR10",
    "codec": "x265",
    "audio": "TrueHD Atmos",
})
print(score.composite)          # e.g. 0.94
print(qa.recommend_profile(score))  # {"name": "Ultra-HD", "cutoff": "2160p"}
```

Published event: `media.quality.scored` with payload `{item_id, composite, dimensions}`.

---

### bandwidth_manager

**Module**: `domains.bandwidth_manager`

Samples network I/O via `psutil`, enforces throttle windows during business hours, and outputs
`rclone --bwlimit` parameters so download clients automatically respect bandwidth budgets.

**Key classes / functions**

| Name | Role |
|------|------|
| `BandwidthManager` | `current_usage() -> BandwidthSample`; `should_throttle() -> bool`; `rclone_params() -> str` |
| `BandwidthSample` | `bytes_sent`, `bytes_recv`, `mbps_sent`, `mbps_recv`, `timestamp` |
| `ThrottleWindow` | Configurable `start_hour` / `end_hour`; checked against `datetime.now().hour` |

**Usage example**

```python
from domains.bandwidth_manager import BandwidthManager

bm = BandwidthManager(
    business_hours_start=9,
    business_hours_end=18,
    default_limit_mbps=100,
    throttle_limit_mbps=20,
)

sample = bm.current_usage()
print(f"Down: {sample.mbps_recv:.1f} Mbps")

if bm.should_throttle():
    print("rclone flags:", bm.rclone_params())   # "--bwlimit 20M"
```

Published events: `media.bandwidth.throttled`, `media.bandwidth.released`.

---

### content_recommender

**Module**: `domains.content_recommender`

Generates content recommendations using Ollama `nomic-embed-text` embeddings and cosine
similarity. Falls back to Jaccard genre overlap when embeddings are unavailable. Integrates
with TMDB for metadata enrichment.

**Key classes / functions**

| Name | Role |
|------|------|
| `ContentRecommender` | `recommend(item_id, top_k=20) -> list[Recommendation]` |
| `EmbeddingCache` | LRU cache (size `embedding_cache_size`); keyed by `item_id` |
| `JaccardFallback` | `similarity(item_a, item_b) -> float` based on genre set intersection |
| `TMDBClient` | `get_metadata(tmdb_id) -> dict` with poster, overview, genres |

**Usage example**

```python
from domains.content_recommender import ContentRecommender

rec = ContentRecommender(ollama_model="nomic-embed-text", top_k=10)
recs = rec.recommend("tt0816692")   # Interstellar

for r in recs:
    print(r.title, f"score={r.score:.3f}", f"method={r.method}")
    # "Arrival  score=0.921  method=embedding"
```

Published event: `media.recommendation.generated` with payload `{item_id, count, method}`.

---

### source_ranker

**Module**: `domains.source_ranker`

Tracks indexer/source health with exponential moving average (EMA, alpha=0.1) and produces a
composite score combining success rate, speed, and quality. Scores are persisted to JSON so
rankings survive restarts.

**Key classes / functions**

| Name | Role |
|------|------|
| `SourceRanker` | `record_outcome(source_id, success, speed_s, quality)` / `ranked() -> list[SourceScore]` |
| `SourceScore` | `source_id`, `success_ema`, `speed_ema`, `quality_ema`, `composite` |
| `ScorePersistence` | Loads/saves `artifacts/source_ranks.json` on each update |

**Composite formula**

```
composite = success_ema × 0.40 + speed_ema × 0.30 + quality_ema × 0.30
```

**Usage example**

```python
from domains.source_ranker import SourceRanker

sr = SourceRanker()
sr.record_outcome("indexer.nzbgeek", success=True, speed_s=1.4, quality=0.9)
sr.record_outcome("indexer.nzbgeek", success=False, speed_s=0.0, quality=0.0)

for s in sr.ranked():
    print(s.source_id, f"composite={s.composite:.3f}")
```

Published event: `media.source.ranked` with payload `{top_source, scores_count}`.

---

### release_scheduler

**Module**: `domains.release_scheduler`

Learns day-of-week / hour-of-day release patterns from historical observations. Confidence
grows as `n / (n + 5)`, reaching ~0.67 at 10 observations. Pre-warms Prowlarr searches
`pre_warm_hours` before the predicted release window.

**Key classes / functions**

| Name | Role |
|------|------|
| `ReleaseScheduler` | `record(show_id, released_at: datetime)`; `predict(show_id) -> Prediction` |
| `Prediction` | `show_id`, `day_of_week`, `hour`, `confidence` |
| `ProwlarrPrewarmer` | `prewarm(show_id, at: datetime)` schedules an `apscheduler` job |
| `CalendarExporter` | `export_ics(path)` writes iCalendar file |

**Usage example**

```python
from domains.release_scheduler import ReleaseScheduler
from datetime import datetime

rs = ReleaseScheduler(min_confidence=0.6, pre_warm_hours=2)
rs.record("show.breaking-bad", datetime(2026, 4, 20, 21, 0))  # Sunday 9pm

pred = rs.predict("show.breaking-bad")
if pred and pred.confidence >= 0.6:
    print(f"Expect release: {pred.day_of_week} ~{pred.hour}:00 (conf={pred.confidence:.2f})")
```

Published event: `media.release.scheduled` with payload `{show_id, day_of_week, hour, confidence}`.

---

## Roadmap Analytics Systems

These five systems analyse the roadmap item corpus in `docs/roadmap/ITEMS/` and provide
planning intelligence.

---

### dependency_analyzer

**Module**: `domains.dependency_analyzer`

Builds a directed dependency graph from roadmap item frontmatter (`depends_on` lists), detects
cycles using Tarjan's strongly connected components, and exports a D3-compatible JSON structure
for visualisation.

**Key classes / functions**

| Name | Role |
|------|------|
| `DependencyAnalyzer` | `build_graph() -> DepGraph`; `cycles() -> list[list[str]]` |
| `DepGraph` | Wraps `networkx.DiGraph`; `bfs(root)`, `ancestors(node)`, `descendants(node)` |
| `D3Exporter` | `export(graph, path)` writes `{nodes, edges}` JSON |

**Usage example**

```python
from domains.dependency_analyzer import DependencyAnalyzer

da = DependencyAnalyzer(items_dir="docs/roadmap/ITEMS")
graph = da.build_graph()

cycles = da.cycles()
if cycles:
    print("Circular dependencies:", cycles)

# Find what blocks a given item
blockers = list(graph.ancestors("RM-EXEC-007"))
print("Blocked by:", blockers)
```

Published event: `roadmap.deps.analyzed` with payload `{node_count, edge_count, cycle_count}`.

---

### effort_predictor

**Module**: `domains.effort_predictor`

Calibrates LOE (Level of Effort) estimates using historical completion-time ratios, computes
p80/p95 estimates via Monte Carlo simulation (1000 runs by default), and projects sprint
completion dates.

**Key classes / functions**

| Name | Role |
|------|------|
| `EffortPredictor` | `predict(item_id) -> EffortEstimate`; `sprint_forecast(items) -> SprintForecast` |
| `EffortEstimate` | `item_id`, `loe`, `p50_days`, `p80_days`, `p95_days` |
| `SprintForecast` | `sprints_needed`, `completion_date`, `confidence_interval` |
| `MonteCarloEngine` | `run(distribution, n=1000) -> Percentiles` |

**Usage example**

```python
from domains.effort_predictor import EffortPredictor

ep = EffortPredictor(monte_carlo_runs=1000, sprint_duration_weeks=2)
est = ep.predict("RM-EXEC-007")
print(f"p80: {est.p80_days:.1f} days, p95: {est.p95_days:.1f} days")

forecast = ep.sprint_forecast(["RM-EXEC-007", "RM-EXEC-008", "RM-TRAIN-003"])
print(f"Completion by sprint {forecast.sprints_needed}: {forecast.completion_date.date()}")
```

Published event: `roadmap.effort.predicted` with payload `{item_id, p80_days, p95_days}`.

---

### priority_engine

**Module**: `domains.priority_engine`

Ranks roadmap items using a weighted priority formula and identifies quick wins (low LOE, high
strategic value) and bottleneck items (high dependency fan-out).

**Priority formula**

```
score = sv × 0.40 + urgency × 0.30 − effort × 0.20 − risk × 0.10 + bottleneck_boost
```

**Key classes / functions**

| Name | Role |
|------|------|
| `PriorityEngine` | `rank(items) -> list[PriorityScore]`; `quick_wins(items) -> list` |
| `PriorityScore` | `item_id`, `score`, `quick_win: bool`, `bottleneck: bool` |
| `PlaneSync` | `sync(scores)` pushes priority updates to Plane; rate-limited to 1.5 req/s |

**Usage example**

```python
from domains.priority_engine import PriorityEngine

pe = PriorityEngine()
scores = pe.rank([
    {"id": "RM-EXEC-007", "sv": 9, "urgency": 7, "effort": 3, "risk": 2},
    {"id": "RM-TRAIN-003", "sv": 6, "urgency": 4, "effort": 8, "risk": 5},
])

for s in scores:
    tag = " [QUICK WIN]" if s.quick_win else ""
    print(f"{s.item_id}: {s.score:.2f}{tag}")
```

Published event: `roadmap.priority.ranked` with payload `{count, top_item_id, quick_wins_count}`.

---

### progress_analytics

**Module**: `domains.progress_analytics`

Derives velocity and burndown / burnup series from `git log` history, then projects a completion
date using Gaussian Monte Carlo (500 runs). Results are cached for 60 seconds to avoid repeated
`git log` calls.

**Key classes / functions**

| Name | Role |
|------|------|
| `ProgressAnalytics` | `velocity() -> float`; `burndown() -> list[DataPoint]`; `forecast() -> date` |
| `DataPoint` | `date`, `remaining`, `completed` |
| `GitHistoryReader` | `commits_since(days=90) -> list[Commit]` |
| `MonteCarloForecast` | `forecast(velocity, remaining, runs=500) -> ForecastResult` |

**Usage example**

```python
from domains.progress_analytics import ProgressAnalytics

pa = ProgressAnalytics(history_days=90)
print(f"Velocity: {pa.velocity():.1f} items/week")

for point in pa.burndown()[-5:]:
    print(f"{point.date}: {point.remaining} remaining")

print(f"Forecast completion: {pa.forecast()}")
```

Published event: `roadmap.progress.updated` with payload `{velocity, remaining, forecast_date}`.

---

### knowledge_graph

**Module**: `domains.knowledge_graph`

Builds a knowledge graph connecting roadmap items, code modules, and concepts. Supports BFS
shortest-path queries, weakly-connected cluster detection, and reverse-BFS impact scoring. Exports
D3 JSON for visualisation in the dashboard.

**Key classes / functions**

| Name | Role |
|------|------|
| `KnowledgeGraph` | `add_node(id, type, attrs)`; `add_edge(src, dst, rel)`; `impact_score(node_id) -> float` |
| `ClusterDetector` | `clusters() -> list[set[str]]` using weakly-connected components |
| `PathFinder` | `shortest_path(src, dst) -> list[str]`; max path length `max_path_length` |
| `D3Exporter` | `export(graph, path)` writes nodes + edges with cluster labels |

**Usage example**

```python
from domains.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph(max_path_length=10, impact_decay=0.8)
kg.add_node("RM-EXEC-007", type="roadmap_item", attrs={"sv": 9})
kg.add_node("framework.parallel_engine", type="module")
kg.add_edge("RM-EXEC-007", "framework.parallel_engine", rel="implements")

print(f"Impact score: {kg.impact_score('RM-EXEC-007'):.3f}")
kg.export_d3("artifacts/knowledge_graph.json")
```

Published event: `roadmap.knowledge.updated` with payload `{node_count, edge_count, cluster_count}`.

---

## Execution Engine Systems

These five systems form the autonomous code-execution pipeline.

---

### parallel_engine

**Module**: `domains.parallel_engine`

Executes task DAGs in parallel using Kahn's topological sort to derive independent layers, then
runs each layer in a `ThreadPoolExecutor`. Auto-scales workers down when CPU utilisation exceeds
80%.

**Key classes / functions**

| Name | Role |
|------|------|
| `ParallelEngine` | `execute(dag: TaskDAG) -> ExecutionResult` |
| `TaskDAG` | `add_task(id, fn, deps=[])` builds the dependency graph |
| `LayerScheduler` | Derives execution layers via Kahn's algorithm |
| `CPUAutoscaler` | Reduces `max_workers` when `psutil.cpu_percent() > cpu_autoscale_threshold` |

**Usage example**

```python
from domains.parallel_engine import ParallelEngine, TaskDAG

dag = TaskDAG()
dag.add_task("fetch_context", fetch_context_fn)
dag.add_task("generate_code", generate_code_fn, deps=["fetch_context"])
dag.add_task("validate", validate_fn, deps=["generate_code"])
dag.add_task("record_trace", trace_fn, deps=["validate"])

engine = ParallelEngine(max_workers=8, task_timeout=300)
result = engine.execute(dag)
print(result.summary())
```

Published events: `executor.task.started`, `executor.task.completed`, `executor.task.failed`.

---

### code_generator

**Module**: `domains.code_generator`

Decomposes natural-language task descriptions into structured code modifications using a local
Ollama model (`qwen2.5-coder:14b`). Retries up to 2 times on syntax errors, and optionally
validates generated code with `ast.parse` and `pylint`.

**Key classes / functions**

| Name | Role |
|------|------|
| `CodeGenerator` | `generate(task: str, context: str) -> list[CodeModification]` |
| `CodeModification` | `target_file`, `operation` (`replace`/`insert`/`delete`), `old_text`, `new_text` |
| `SyntaxValidator` | `validate(code: str) -> bool` using `ast.parse` |
| `OllamaDecomposer` | Sends prompt to Ollama, parses JSON array response |

**Usage example**

```python
from domains.code_generator import CodeGenerator

cg = CodeGenerator(ollama_model="qwen2.5-coder:14b", max_retries=2)
mods = cg.generate(
    task="Add a guard clause to ExecutorFactory.__init__ that raises ValueError when no executor is available",
    context=open("framework/code_executor.py").read(),
)

for mod in mods:
    print(f"  {mod.target_file}: {mod.operation}")
```

Published events: `codegen.task.generated`, `codegen.task.validated`.

---

### context_manager

**Module**: `domains.context_manager`

Scores repository files for relevance to a query using import-count weighting, query-token hit
counting, and a 30-day recency half-life decay. Enforces a 25% per-file token cap to prevent any
single file from dominating the context window.

**Key classes / functions**

| Name | Role |
|------|------|
| `ContextManager` | `select_files(query: str, budget_tokens=8000) -> list[ContextFile]` |
| `ContextFile` | `path`, `score`, `token_count`, `reason` |
| `RecencyDecay` | `decay(file_path) -> float` computes `0.5 ** (age_days / 30)` |
| `TokenEstimator` | `count(text: str) -> int` using 4-chars-per-token heuristic |

**Usage example**

```python
from domains.context_manager import ContextManager

cm = ContextManager(max_context_tokens=8000, single_file_cap=0.25)
files = cm.select_files(
    query="improve ExecutorFactory circuit breaker logic",
    budget_tokens=6000,
)

for f in files:
    print(f.path, f"score={f.score:.3f}", f"tokens={f.token_count}")
```

Published event: `context.files.selected` with payload `{query, file_count, total_tokens}`.

---

### recovery_engine

**Module**: `domains.recovery_engine`

Matches execution errors against 7 regex patterns (syntax error, import error, timeout, file
not found, permission denied, out of memory, assertion failure) and selects a recovery strategy.
Strategy success rates are tracked with EMA so the best strategy rises over time.

**Key classes / functions**

| Name | Role |
|------|------|
| `RecoveryEngine` | `recover(error: str, context: dict) -> RecoveryAction` |
| `RecoveryAction` | `strategy`, `params`, `confidence` |
| `ErrorClassifier` | `classify(error_text) -> ErrorClass` via 7-pattern regex matching |
| `StrategySelector` | Picks strategy with highest EMA success rate for the error class |

**Strategies**

| Strategy | Trigger |
|----------|---------|
| `fix_syntax` | `SyntaxError`, `IndentationError` |
| `install_missing` | `ModuleNotFoundError`, `ImportError` |
| `extend_timeout` | Task timeout exceeded |
| `rollback` | Unrecoverable file corruption |
| `partial_save` | Out-of-memory; saves completed sub-tasks |

**Usage example**

```python
from domains.recovery_engine import RecoveryEngine

re = RecoveryEngine()
action = re.recover(
    error="ModuleNotFoundError: No module named 'networkx'",
    context={"task_id": "dep-analysis-01"},
)
print(action.strategy, action.params)  # install_missing {'package': 'networkx'}
```

Published event: `recovery.strategy.applied` with payload `{error_class, strategy, success}`.

---

### execution_tracer

**Module**: `domains.execution_tracer`

Records every step of an execution run: step name, timestamp, inputs/outputs, and a full
file-content snapshot. Generates `difflib` unified diffs between before/after snapshots. Exports
traces as JSON or human-readable Markdown.

**Key classes / functions**

| Name | Role |
|------|------|
| `ExecutionTracer` | `start_trace(run_id)` / `record_step(name, data)` / `end_trace() -> Trace` |
| `Trace` | `run_id`, `steps[]`, `snapshots[]`, `diffs[]`, `duration_s` |
| `FileSnapshot` | `path`, `content`, `size_bytes`, `captured_at` |
| `TraceExporter` | `to_json(trace, path)` / `to_markdown(trace, path)` |

**Usage example**

```python
from domains.execution_tracer import ExecutionTracer

tracer = ExecutionTracer(trace_dir="artifacts/traces/")
tracer.start_trace(run_id="run-2026-04-25-001")

tracer.record_step("fetch_context", {"files": ["framework/code_executor.py"]})
tracer.record_step("generate_code", {"modifications": 3})

trace = tracer.end_trace()
tracer.export(trace, format="markdown")   # artifacts/traces/run-2026-04-25-001.md
```

Published event: `tracer.trace.completed` with payload `{run_id, step_count, duration_s}`.

---

## Training Systems

These four systems support ML model training workflows on the Mac Studio (GPU/MPS) node.

> **Note**: ML dependencies (`torch`, `transformers`) live in `~/training-env` (virtualenv).
> Never install them into the main project environment. See `docs/TRAINING.md`.

---

### hyperparam_tuner

**Module**: `domains.hyperparam_tuner`

UCB-based (Upper Confidence Bound) hyperparameter search. The first 5 trials are random
exploration; thereafter, 70% of trials exploit the best-known region (Gaussian sampling in
log-scale for `learning_rate`/`weight_decay`, linear for others) and 30% remain random.
Supports early stopping with configurable patience.

**Key classes / functions**

| Name | Role |
|------|------|
| `HyperparamTuner` | `suggest() -> HyperparamSet`; `report(params, score)`; `best() -> HyperparamSet` |
| `HyperparamSet` | Dict-like mapping of param name → value |
| `UCBSampler` | Balances exploitation vs. exploration via UCB score |
| `EarlyStoppingGuard` | Raises `StopTuning` after `patience` non-improving trials |

**Usage example**

```python
from domains.hyperparam_tuner import HyperparamTuner

tuner = HyperparamTuner(
    param_space={
        "learning_rate": (1e-5, 1e-2, "log"),
        "batch_size": (16, 128, "linear"),
        "warmup_steps": (0, 500, "linear"),
    },
    first_random_trials=5,
    exploit_ratio=0.70,
    patience=5,
)

for trial in range(30):
    params = tuner.suggest()
    score = train_one_epoch(**params)   # your training function
    tuner.report(params, score)

print("Best params:", tuner.best())
```

Published event: `training.hyperparams.selected` with payload `{trial, params, score}`.

---

### checkpoint_mgr

**Module**: `domains.checkpoint_mgr`

Saves model checkpoints using `torch.save` with a `pickle` fallback for non-torch objects.
Scores checkpoints using `0.70 × val_loss − 0.30 × f1` (lower is better) and prunes to keep
only the top `max_keep` (default 5) plus the latest.

**Key classes / functions**

| Name | Role |
|------|------|
| `CheckpointManager` | `save(model, epoch, metrics) -> CheckpointMeta`; `best() -> CheckpointMeta`; `prune()` |
| `CheckpointMeta` | `path`, `epoch`, `score`, `metrics`, `saved_at` |
| `CompositeScorer` | `score(val_loss, f1) -> float` — lower = better |

**Usage example**

```python
from domains.checkpoint_mgr import CheckpointManager

ckpt_mgr = CheckpointManager(
    checkpoint_dir="artifacts/checkpoints/",
    max_keep=5,
)

for epoch in range(100):
    val_loss, f1 = evaluate(model)
    meta = ckpt_mgr.save(model, epoch=epoch, metrics={"val_loss": val_loss, "f1": f1})
    ckpt_mgr.prune()

best = ckpt_mgr.best()
print(f"Best checkpoint: {best.path}  (epoch {best.epoch}, score {best.score:.4f})")
```

Published events: `training.checkpoint.saved`, `training.checkpoint.pruned`.

---

### training_viz

**Module**: `domains.training_viz`

Appends per-epoch metrics to a JSONL log, detects overfitting (val_loss increasing for
`overfitting_window` consecutive epochs), tracks gradient explosion / vanishing, and provides
the live `/api/training/viz` endpoint for dashboard streaming.

**Key classes / functions**

| Name | Role |
|------|------|
| `TrainingViz` | `log_epoch(metrics: dict)`; `overfitting_detected() -> bool`; `gradient_stats(grads)` |
| `EpochRecord` | `epoch`, `loss`, `val_loss`, `f1`, `lr`, `grad_norm`, `timestamp` |
| `OverfittingDetector` | Checks if `val_loss` has increased for the last `overfitting_window` epochs |
| `GradientMonitor` | Flags explosion (`norm > 100`) or vanishing (`norm < 1e-7`) |

**Usage example**

```python
from domains.training_viz import TrainingViz

viz = TrainingViz(
    log_path="artifacts/training_log.jsonl",
    overfitting_window=3,
)

for epoch in range(100):
    loss = train_one_epoch(model)
    val_loss, f1 = evaluate(model)
    grad_norm = compute_gradient_norm(model)

    viz.log_epoch({"epoch": epoch, "loss": loss, "val_loss": val_loss,
                   "f1": f1, "lr": scheduler.get_last_lr()[0], "grad_norm": grad_norm})

    if viz.overfitting_detected():
        print(f"Overfitting at epoch {epoch} — consider early stopping")
        break
```

Published events: `training.epoch.logged`, `training.overfitting.detected`.

---

### distributed_prep

**Module**: `domains.distributed_prep`

Detects available GPU/MPS devices (`torch.cuda`, `nvidia-smi`, MPS availability), generates
PyTorch DDP initialisation code for the detected topology, and produces a `torchrun` launch
command. Defaults to `gloo` backend on CPU and MPS (Mac Studio), `nccl` on CUDA.

**Key classes / functions**

| Name | Role |
|------|------|
| `DistributedPrep` | `detect() -> DeviceTopology`; `generate_init_code() -> str`; `torchrun_cmd() -> str` |
| `DeviceTopology` | `backend`, `world_size`, `device_type` (`cuda`/`mps`/`cpu`) |
| `DDPCodeGenerator` | Renders `dist.init_process_group(...)` and `DistributedDataParallel(...)` boilerplate |

**Usage example**

```python
from domains.distributed_prep import DistributedPrep

dp = DistributedPrep()
topology = dp.detect()
print(f"Device: {topology.device_type}, backend: {topology.backend}, world_size: {topology.world_size}")

# Get DDP init boilerplate to embed in training script
init_code = dp.generate_init_code()
print(init_code)

# Get the torchrun launch command
cmd = dp.torchrun_cmd(script="train.py", extra_args="--epochs 50")
print(cmd)   # torchrun --nproc_per_node=1 train.py --epochs 50
```

Published event: `training.distributed.configured` with payload `{device_type, backend, world_size}`.

---

## Event Bus Conventions

### Naming convention

All events follow the pattern `domain.noun.verb` using lowercase and dots:

```
<domain>.<noun>.<verb>
```

| Segment | Examples |
|---------|----------|
| domain | `media`, `roadmap`, `executor`, `codegen`, `context`, `recovery`, `tracer`, `training` |
| noun | `quality`, `bandwidth`, `recommendation`, `source`, `release`, `deps`, `effort`, `priority`, `progress`, `knowledge`, `task`, `checkpoint`, `epoch` |
| verb | `scored`, `throttled`, `released`, `generated`, `ranked`, `scheduled`, `analyzed`, `predicted`, `updated`, `started`, `completed`, `failed`, `selected`, `applied`, `saved`, `pruned`, `logged`, `detected`, `configured` |

**Full event inventory** (from `config/systems.yaml`)

```
media.quality.scored          media.bandwidth.throttled     media.bandwidth.released
media.recommendation.generated  media.source.ranked         media.release.scheduled
roadmap.deps.analyzed         roadmap.effort.predicted      roadmap.priority.ranked
roadmap.progress.updated      roadmap.knowledge.updated
executor.task.started         executor.task.completed       executor.task.failed
codegen.task.generated        codegen.task.validated        context.files.selected
recovery.strategy.applied     tracer.trace.completed
training.hyperparams.selected training.checkpoint.saved     training.checkpoint.pruned
training.epoch.logged         training.overfitting.detected training.distributed.configured
```

### Subscribing to events

```python
from framework.event_system import EventBus

bus = EventBus()

# Exact match
bus.subscribe("media.quality.scored", handler_fn)

# Wildcard — all media events
bus.subscribe("media.*.*", handler_fn)

# Wildcard — all task events across domains
bus.subscribe("*.task.*", handler_fn)

# Unsubscribe
bus.unsubscribe("media.quality.scored", handler_fn)
```

### Publishing events

Systems should publish via the singleton bus, never instantiate a new one:

```python
from framework.event_system import EventBus, Event

EventBus().publish(Event(
    name="media.quality.scored",
    payload={"item_id": "tt1234567", "composite": 0.87},
    source="quality_analyzer",
))
```

### Dead-letter queue

If a subscriber raises an exception, the event is moved to the DLQ. Inspect it via:

```python
dlq_events = EventBus().dlq.drain()
for ev in dlq_events:
    print(ev.name, ev.error)
```

---

## Metrics Convention

All metrics use the `iap_` prefix (configurable via `prometheus_prefix` in
`config/systems.yaml`). Systems emit metrics using the shared `MetricsRegistry` singleton.

### Naming pattern

```
iap_<system>_<noun>_<unit>
```

Examples:

| Metric name | Type | Emitted by |
|-------------|------|------------|
| `iap_quality_score_total` | Counter | quality_analyzer |
| `iap_bandwidth_mbps` | Gauge | bandwidth_manager |
| `iap_recommendation_latency_ms` | Histogram | content_recommender |
| `iap_task_completed_total` | Counter | parallel_engine |
| `iap_checkpoint_score` | Gauge | checkpoint_mgr |
| `iap_training_epoch_loss` | Gauge | training_viz |

### Emitting from a domain system

```python
from framework.metrics_system import MetricsRegistry

reg = MetricsRegistry()
score_counter = reg.counter("iap_quality_score_total")
latency_hist   = reg.histogram("iap_quality_score_latency_ms")

import time
start = time.time()
score = compute_score(item)
latency_hist.observe((time.time() - start) * 1000)
score_counter.increment()
```

### Prometheus scrape

The `/api/metrics?format=prometheus` endpoint returns standard Prometheus text:

```
# HELP iap_quality_score_total Total quality scores computed
# TYPE iap_quality_score_total counter
iap_quality_score_total 1234
# HELP iap_bandwidth_mbps Current network bandwidth usage
# TYPE iap_bandwidth_mbps gauge
iap_bandwidth_mbps 42.3
```

Recommended `prometheus.yml` scrape config:

```yaml
scrape_configs:
  - job_name: iap
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: /api/metrics
    params:
      format: [prometheus]
```

---

## Configuration

### How config/systems.yaml works

`config/systems.yaml` is the single source of truth for all 26 systems. It is loaded at
startup by `framework.config_system.ConfigLoader` and deep-merged with any environment-specific
overlay.

**Structure**

```yaml
meta:          # version, last_updated, total_systems
framework:     # 5 infrastructure systems
  <system_key>:
    module:         # Python import path
    description:    # One-line description
    api_endpoint:   # HTTP endpoint (if any)
    config:         # System-specific config keys
    events:         # publishes / subscribes lists
media_intelligence:   # 5 systems
roadmap_analytics:    # 5 systems
execution_engine:     # 5 systems
training:             # 4 systems
```

### Reading config in a domain system

```python
from framework.config_system import ConfigLoader

loader = ConfigLoader(config_dir="config/")
cfg = loader.load("systems.yaml")

# Get this system's config block
my_cfg = cfg["media_intelligence"]["quality_analyzer"]["config"]
weights = my_cfg["score_weights"]   # {"resolution": 0.30, ...}
```

### Per-environment overrides

Create `config/systems.local.yaml` (gitignored) or `config/systems.prod.yaml`. The
`ConfigLoader` deep-merges the overlay on top of the base:

```yaml
# config/systems.local.yaml — developer overrides
media_intelligence:
  content_recommender:
    config:
      top_k: 5          # reduce for local testing
      cache_embeddings: false

training:
  hyperparam_tuner:
    config:
      first_random_trials: 2   # faster iteration locally
```

Load with:

```python
cfg = loader.load("systems.yaml", overlay="systems.local.yaml")
```

### Encrypted secrets

Sensitive values (API keys, tokens) can be stored encrypted in YAML using `ENC[...]` syntax:

```yaml
# config/connectors.yaml
sonarr:
  api_key: "ENC[gAAAAABh...]"
```

At load time, `ConfigEncryption` decrypts them transparently when `CONFIG_ENCRYPTION_KEY` is set
in the environment. Generate a key pair with:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Hot reload

Enable configuration hot reload so running processes pick up changes without restart:

```python
loader = ConfigLoader(config_dir="config/")
cfg = loader.load("systems.yaml")

def on_reload(new_cfg):
    # Update live config references
    bandwidth_manager.update_config(new_cfg["media_intelligence"]["bandwidth_manager"]["config"])

loader.watch(callback=on_reload, interval=5)   # checks every 5 seconds
```
