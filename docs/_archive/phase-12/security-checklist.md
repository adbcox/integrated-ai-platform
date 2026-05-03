# Zabbix Security Hardening Checklist

## COMPLETE ON FIRST LOGIN

- [ ] Change default admin password (Admin / zabbix → strong password)
- [ ] Disable guest access: Administration → Authentication
- [ ] Create read-only Grafana user: grafana_reader
- [ ] Configure housekeeping periods (30d history, 365d trends)

## NETWORK SECURITY

- [ ] OPNsense firewall rule: only 192.168.10.145 can reach SNMP :161/udp on .1 and .201
- [ ] Port 10051 (Zabbix trapper) not exposed externally
- [ ] Web UI :10080 accessible from LAN only

## AGENT ENCRYPTION

- [ ] Mac Mini native agent: PSK encryption (Mac-Mini-M4-PSK)
- [ ] Mac Studio (when delivered): PSK encryption (Mac-Studio-M3-PSK)

## BACKUPS

```bash
# Manual backup
docker exec zabbix-postgres pg_dump -U zabbix zabbix | \
  gzip > ~/backups/zabbix-$(date +%Y%m%d).sql.gz

# Cleanup old backups
find ~/backups/zabbix-*.sql.gz -mtime +30 -delete
```

## MONITORING

- Weekly: Administration → Audit log review
- Monthly: Failed login check
- Quarterly: User permission review
