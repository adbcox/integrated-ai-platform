# Mac Mini Native Agent Setup

The `zabbix-agent` container runs inside Docker and monitors the container environment.
For full macOS host-level metrics, install the native agent:

## Install Native Zabbix Agent

```bash
# Download ARM64 agent for macOS
curl -o /tmp/zabbix-agent.pkg \
  https://cdn.zabbix.com/zabbix/binaries/stable/7.4/7.4.0/zabbix_agent-7.4.0-macos-arm64-openssl.pkg

sudo installer -pkg /tmp/zabbix-agent.pkg -target /

# Generate PSK
openssl rand -hex 128 | sudo tee /usr/local/etc/zabbix/agent.psk
sudo chmod 600 /usr/local/etc/zabbix/agent.psk
PSK_VALUE=$(sudo cat /usr/local/etc/zabbix/agent.psk)
echo "PSK: $PSK_VALUE"
```

## Configure Agent

```bash
sudo tee /usr/local/etc/zabbix/zabbix_agentd.conf << 'EOF'
Server=192.168.10.145
ServerActive=192.168.10.145
Hostname=Mac-Mini-M4-Pro
ListenIP=192.168.10.145
ListenPort=10050
TLSConnect=psk
TLSAccept=psk
TLSPSKIdentity=Mac-Mini-M4-PSK
TLSPSKFile=/usr/local/etc/zabbix/agent.psk
LogFile=/var/log/zabbix/zabbix_agentd.log
EOF

sudo mkdir -p /var/log/zabbix
sudo launchctl load /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist
```

## In Zabbix Web UI

Configuration → Hosts → Create host:
- Host name: Mac-Mini-M4-Pro
- Templates: macOS by Zabbix agent
- Interface: Agent, 192.168.10.145:10050
- Encryption tab: PSK, Identity = Mac-Mini-M4-PSK, Value = [from above]
