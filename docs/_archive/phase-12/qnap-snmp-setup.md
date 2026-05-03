# QNAP NAS SNMP Configuration

## ON QNAP NAS (192.168.10.201)

### 1. Enable SNMP
Control Panel → Network & File Services → SNMP:
- Enable SNMP Service: ✅
- SNMP Version: SNMPv2
- Community (Read): zabbix_monitor
- Allowed Clients: 192.168.10.145
- Click "Apply"

### 2. Test from Mac Mini
```bash
docker exec zabbix-server snmpwalk -v2c -c zabbix_monitor 192.168.10.201 system
```

## IN ZABBIX WEB UI (http://192.168.10.145:10080)

### Create Host
Configuration → Hosts → Create host
- Host name: QNAP-NAS
- Templates: Template Net QNAP NAS SNMPv2
- Groups: Storage devices
- Interface: SNMP, IP 192.168.10.201, Port 161, SNMPv2, community {$SNMP_COMMUNITY}

### Configure Macros
Hosts → QNAP-NAS → Macros:
- {$SNMP_COMMUNITY} = zabbix_monitor

### Expected Metrics
Monitoring → Latest data → Filter: QNAP-NAS
Should see: Volume status, Disk info, Temperature, Network within 5-10 minutes
