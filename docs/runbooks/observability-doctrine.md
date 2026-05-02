# Observability Doctrine

The platform runs two metrics stacks intentionally. Each owns a
distinct capability set. Together they cover the platform's
observability surface. This document is canonical; the two
capability audits (`docs/audits/capability/zabbix-2026-05-01.md`
and `docs/audits/capability/victoriametrics-2026-05-01.md`) are the
evidence.

---

## Authoritative roles

### Zabbix (5 containers — server, agent, web, postgres, exporter)

Owns:
- **Network device monitoring** — SNMP polling. 4,593 SNMP items
  across 55 hosts (OPNsense, switches, UPS, network gear).
- **JMX-instrumented application monitoring** — 510 JMX items.
- **Infrastructure trigger/alert configuration** — 7,198 active
  triggers using Zabbix's expression language (state machines,
  dependency hierarchies, SNMP-trap-driven rules).
- **Hosts not running Prometheus exporters** — anything that needs
  agentless polling or vendor-specific protocols.
- **Devices outside Docker** — physical infrastructure where a
  Prometheus exporter container can't be deployed (OPNsense, QNAP,
  switches, UPS).

### VictoriaMetrics + vmagent (4 containers — vm, vmagent, node-exporter, cadvisor)

Owns:
- **Container metrics** — cAdvisor exposes per-cgroup CPU, memory,
  network, disk for Docker-native services.
- **Host metrics** — node-exporter exposes Mac Mini host-level
  CPU, load, memory, disk, network, filesystems.
- **Service-exposed `/metrics` endpoints** — Caddy, mcp-docs, and
  any future service that exposes Prometheus-format metrics.
- **Time-series ad-hoc query (PromQL)** — Grafana queries this for
  dashboards and alerting.
- **Long-term retention for capacity planning** — single-node `vm`
  container holds 170,752 series (cardinality at 2026-05-01).

---

## Boundary rule

When deploying a new service, decide which stack monitors it:

1. **Service is in Docker AND exposes `/metrics`?** → VictoriaMetrics.
   Add a scrape job to vmagent's config.
2. **Service is a network device, SNMP-capable, or Java/JMX?**
   → Zabbix. Register the host and apply the appropriate template.
3. **Both could work, no clear preference?** → VictoriaMetrics
   (default — container-stack-native, lower friction, PromQL is
   Grafana-first).

This default exists to prevent re-litigating the choice for every
new service. Override it only with documented reason.

---

## Bridge between stacks

`zabbix-exporter` (Phase 14 D-ZBX, custom container) was built to
bridge Zabbix → VictoriaMetrics so PromQL could query Zabbix state
(trigger counts by severity, host availability counts).

**Status at D-17-05 (2026-05-01):** the bridge is unreliable. It
intermittently times out on the underlying Zabbix API calls
(`trigger.get` with `monitored:1` returns 7,198 records;
`host.get` returns 55 records — both can exceed the exporter's
15-second URL-open timeout under load). Successful scrapes still
happen, but `docker logs zabbix-exporter` shows continuous
`Collect error: timed out` lines between them.

**Decision:** **RETIRE the bridge.**

Justification:
- The bridge exposes only **2 metrics** (`zabbix_triggers_active`,
  `zabbix_hosts_available`).
- Grafana already has a **native Zabbix data source** configured;
  panels can query Zabbix directly without translation through
  Prometheus.
- Cross-stack PromQL over those 2 metrics is not load-bearing —
  no dashboard or alert rule depends on querying Zabbix state via
  PromQL.
- Maintaining the bridge means: diagnosing per-call timeouts,
  potentially adding pagination/scoping to the exporter,
  re-authenticating on token rotation. Cost without benefit.
- Zabbix data continues to live in Zabbix and is queryable via
  Grafana's Zabbix data source. No data is lost.

**Migration:**
- Remove `zabbix-exporter` from compose (Phase 14 D-ZBX compose).
- Remove the `zabbix-exporter` scrape job from vmagent's config.
- The 2 retired metrics in VictoriaMetrics will age out per
  retention policy.
- Any Grafana panel that consumed those metrics — none currently
  identified — would be re-pointed at the Zabbix data source.

Effort: ~30 minutes once the operator approves the compose change
(operator-confirmation gate per CLAUDE.md compose-edit rule).

---

## Narrow overlap — Zabbix-agent type-0 items vs node-exporter

Zabbix collects 706 type-0 items (Zabbix-agent passive checks). A
sample of the keys collected:

```
kernel.maxfiles, kernel.maxproc
proc.num[], proc.num[,,run]
system.boottime, system.localtime, system.hostname
system.cpu.intr, system.cpu.switches
system.cpu.load[percpu,avg1|avg5|avg15]
system.cpu.util[,user|system|nice|idle|interrupt]
system.swap.size[,free|pfree|total]
```

These overlap heavily (~80%+) with what node-exporter exposes for
the Mac Mini:

| Zabbix-agent key | node-exporter equivalent |
|---|---|
| `system.cpu.util[,user]` | `node_cpu_seconds_total{mode="user"}` |
| `system.cpu.util[,system]` | `node_cpu_seconds_total{mode="system"}` |
| `system.cpu.load[percpu,avg1]` | `node_load1` (with cpu-count divisor) |
| `system.swap.size[,free]` | `node_memory_SwapFree_bytes` |
| `system.boottime` | `node_boot_time_seconds` |
| `system.hostname` | `node_uname_info{nodename=...}` |
| `proc.num[]` | `node_procs_running` + `node_procs_blocked` |

**Disposition:** documented as known narrow duplication. NOT
retired in this turn because:
- Retiring 706 items from Zabbix would break the templates that
  reference them and any triggers built on those templates.
- node-exporter and Zabbix-agent both work today; the duplication
  costs disk (TimescaleDB rows) but no runtime risk.
- The cleanup is item-level (Zabbix template editing), not a
  doctrine question. Tracked as a follow-up under Zabbix audit
  Section 4 ("Queued cleanup").

When the operator decides to do that cleanup, it's a Zabbix-side
template edit — not a stack-architecture decision.

---

## Operating notes

- **Adding a Grafana dashboard** that needs both metric stacks: use
  Grafana's built-in mixed-data-source feature (one panel per
  source) rather than expecting cross-stack PromQL.
- **Alert routing**: PromQL threshold rules → Grafana alerting →
  ntfy. SNMP/state-machine rules → Zabbix triggers → Zabbix actions
  (currently webhook → ntfy; minimal use today).
- **On-call**: until separate on-call doctrine exists, both stacks
  feed the same ntfy topic; operator filters by message body.

---

## Decision log

- **Authored:** 2026-05-01 (D-17-05)
- **Reviewed by operator:** yes
- **Linked artifacts:**
  - `docs/audits/capability/zabbix-2026-05-01.md` (D-17-02 / D-17-05)
  - `docs/audits/capability/victoriametrics-2026-05-01.md` (D-17-05)
  - `docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` Layer 8 (D-17-01)
  - D#20 (capability evidence)
- **Refresh trigger:** when either stack changes role, when a third
  metrics tool is proposed, or at phase boundary (D#19).
