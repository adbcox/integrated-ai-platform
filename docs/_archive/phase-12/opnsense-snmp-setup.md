# OPNsense SNMP Configuration

## ON OPNSENSE (192.168.10.1)

### 1. Enable bsnmpd Service
SSH to OPNsense or use Web UI → Services → Net-SNMP:

```bash
# Via SSH if preferred
echo 'bsnmpd_enable="YES"' > /etc/rc.conf.d/bsnmpd
vi /etc/snmpd.conf
# Uncomment hostres and pf modules
# Change community: read := "zabbix_monitor"
/etc/rc.d/bsnmpd start
```

Via Web UI: Services → Net-SNMP → Enable, community = zabbix_monitor, allowed client = 192.168.10.145

### 2. Firewall Rule
Firewall → Rules → LAN:
- Action: Pass, Protocol: UDP
- Source: 192.168.10.145, Destination Port: 161 (SNMP)
- Description: Zabbix SNMP Monitoring

### 3. Test from Mac Mini
```bash
docker exec zabbix-server snmpwalk -v2c -c zabbix_monitor 192.168.10.1 system
```

## IN ZABBIX WEB UI (http://192.168.10.145:10080)

### Create Host
Configuration → Hosts → Create host
- Host name: OPNsense-Firewall
- Templates: OPNsense by SNMP (or Network Generic Device SNMPv2)
- Groups: Network devices
- Interface: SNMP, IP 192.168.10.1, Port 161, SNMPv2, community {$SNMP_COMMUNITY}

### Configure Macros
Hosts → OPNsense-Firewall → Macros:
- {$SNMP_COMMUNITY} = zabbix_monitor
