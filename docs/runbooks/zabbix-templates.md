# Zabbix Templates

Canonical template inventory for the Zabbix 7.4 deployment on Mac Mini.

## Download pipeline

- `Template Download Pipeline HTTP` — arr queue/health, SAB queue/failed jobs, Syncthing trapper items for the Mac Mini pipeline host.

## QNAP Syncthing

- `Template QNAP Syncthing HTTP` — QNAP Syncthing REST monitoring on host `qnap-ts-x72`.
- Source: `config/zabbix/templates/qnap-syncthing.yaml`
- Provisioner: `scripts/provision-zabbix-qnap-syncthing.py`
- Collector: `scripts/qnap-syncthing-zabbix-sender.sh`
- Transport: Mac Mini collector polls the REST API and pushes trapper items; no Zabbix agent installation required on QNAP.

## Notes

1. Use template-level macros for shared endpoints and thresholds.
2. Keep credential values out of the repository; populate API-key macros at provision time from Vault paths.
3. Prefer HTTP-agent items for LAN-reachable services; use trapper items when the service is network-filtered from the Zabbix server container but reachable from the Mac Mini host.
