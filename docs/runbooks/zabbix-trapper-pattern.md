# Zabbix Trapper Pattern (Loopback-Bound Services)

Date: 2026-05-04
Primary example: D-17-105 Syncthing on QNAP

## When to use this pattern

Use trapper items when Zabbix HTTP agent cannot reach a service directly, especially when:

1. Service API is loopback-bound on a remote host (`127.0.0.1` only).
2. Container/network segmentation blocks direct poll.
3. Changing service bind address is risky or non-durable.

## Architecture

1. Collector runs from a trusted host (Mac Mini).
2. Collector SSHes to remote host and queries loopback API locally.
3. Collector parses metrics and pushes values with `zabbix_sender`.
4. Zabbix stores values in trapper items (`type=2`) on target host.

## D-17-105 implementation

- Collector: `scripts/syncthing-zabbix-sender.sh`
- Push target host: `mac-mini` (hostid 10783)
- Keys:
  - `d17105.syncthing.qnap.state`
  - `d17105.syncthing.qnap.last_completed_ts`
  - `d17105.syncthing.qnap.errors_total`
  - `d17105.syncthing.qnap.max_stale_h`

## Scheduler

Current schedule (macmini cron, every 5 minutes):

```cron
*/5 * * * * /Users/admin/repos/integrated-ai-platform/scripts/syncthing-zabbix-sender.sh >> /Users/admin/.platform-logs/syncthing-zabbix-sender.log 2>&1
```

## Operational notes

1. Keep trapper items free of preprocessing whenever possible.
2. Cache API key locally with strict perms (`0600`) to reduce Vault roundtrips.
3. Push sentinel values (`-1` or state `2`) when probe fails, so alerts can fire.
4. Verify sender path with:
   - `zabbix_sender -vv -z 127.0.0.1 -p 10051 ...`
   - `item.get` (`lastvalue`, `lastclock`, `state`) via Zabbix API.
