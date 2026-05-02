# RETIRED — zabbix-exporter

**Retired:** 2026-05-01 in deliverable 17.E.

## Why retired

The exporter bridged Zabbix → Prometheus by exposing two metrics:
`zabbix_triggers_active{severity}` and `zabbix_hosts_available{status}`.
It was unreliable in production: the `zbx_post()` helper used a 15s
`urlopen` timeout, but `trigger.get` (returning 7,198 records) and
`host.get` regularly exceeded that timeout under load. The container
stayed Docker-`healthy` because the HTTP server kept serving stale
data, masking the failure.

The bridge had low value relative to its maintenance cost:

- Only 2 metrics were exposed.
- Grafana already has a native Zabbix data source — panels can query
  Zabbix directly without the Prometheus translation hop.
- No load-bearing dashboard or alert depends on cross-stack PromQL
  over Zabbix data.

See `docs/runbooks/observability-doctrine.md` §"Bridge between
stacks" for the canonical decision and rationale, and
`docs/audits/capability/zabbix-2026-05-01.md` Section 2.4 for the
audit-trail entry.

## Restoration

If a future need re-justifies a Zabbix→Prometheus bridge:

1. Move this directory back to `docker/zabbix-exporter/`.
2. Re-add the scrape job to `docker/vmagent-config/scrape.yml`:
   ```
   - job_name: zabbix-exporter
     static_configs:
       - targets: ['host.docker.internal:9224']
         labels:
           service: zabbix
   ```
3. Reload vmagent (`curl -XPOST http://127.0.0.1:8429/-/reload`).
4. **Re-evaluate first.** The native Grafana Zabbix data source
   covers the visualization use case without the timeout fragility.
   If you still need PromQL queries over Zabbix state, fix the
   timeout in `exporter.py` (paginate `trigger.get`, scope by
   priority, raise the timeout to ≥60s) BEFORE redeploying.

The `iap/zabbix-exporter:phase14` Docker image remains on disk
locally; next image-cleanup pass will remove orphans.

## Provenance

- Originated: Phase 14 D-ZBX (Prometheus exposition for Zabbix state).
- Retired: 17.E (observability role-clarification, 2026-05-01).
