# Grafana-Zabbix Integration

## Install Plugin

```bash
docker exec grafana grafana-cli plugins install alexanderzobnin-zabbix-app
docker restart grafana
```

## Configure Data Source in Grafana UI (http://192.168.10.145:3030)

1. Configuration → Data sources → Add data source → Search "Zabbix"
2. URL: http://192.168.10.145:10080/api_jsonrpc.php
3. Auth type: User login
4. Username: grafana_reader
5. Password: [password set in Zabbix UI]
6. Enable "Trends" + "Direct DB Connection"
7. Click "Save & test"

## PostgreSQL Direct Connection (for raw queries)

Add a second data source:
- Type: PostgreSQL
- Host: 192.168.10.145:5432 (from outside Docker) or zabbix-postgres:5432 (from same Docker network)
- Database: zabbix
- User: grafana_reader (needs DB read access - grant via psql)
- SSL Mode: disable

Grant read access:
```sql
-- Run in zabbix-postgres
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;
```

## Add to Homarr Dashboard

Homarr (http://192.168.10.145:7575):
- Add widget → iframe
- URL: http://192.168.10.145:3030/d/zabbix-overview
- Tab: "Monitoring"
