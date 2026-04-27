#!/bin/bash
# Mac Mini Zabbix Agent Installer
# Run with: bash install-mac-agent.sh
# (requires sudo password)

set -e
PSK_KEY="1939b436368d7c971567d07aef8ddb94027860315a0b4e7cbb3397974e3e5c3d"
PSK_IDENTITY="mac-mini-m4-pro-psk"

echo "Installing Zabbix Agent 7.4.9..."
sudo installer -pkg ~/Downloads/zabbix_agent-7.4.9-macos-arm64-openssl.pkg -target /

echo "Writing PSK file..."
sudo mkdir -p /usr/local/etc/zabbix
printf '%s' "$PSK_KEY" | sudo tee /usr/local/etc/zabbix/agent.psk > /dev/null
sudo chmod 600 /usr/local/etc/zabbix/agent.psk
sudo chown root:wheel /usr/local/etc/zabbix/agent.psk

echo "Writing agent config..."
sudo tee /usr/local/etc/zabbix/zabbix_agentd.conf > /dev/null << 'EOF'
Server=192.168.10.145
ServerActive=192.168.10.145
Hostname=mac-mini-m4-pro
ListenIP=192.168.10.145
ListenPort=10050
TLSConnect=psk
TLSAccept=psk
TLSPSKIdentity=mac-mini-m4-pro-psk
TLSPSKFile=/usr/local/etc/zabbix/agent.psk
LogFile=/var/log/zabbix/zabbix_agentd.log
LogFileSize=10
DebugLevel=3
EOF

sudo mkdir -p /var/log/zabbix

echo "Starting agent..."
sudo launchctl unload /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist 2>/dev/null || true
sudo launchctl load /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist

sleep 2
if ps aux | grep -v grep | grep -q zabbix_agentd; then
    echo "✅ Zabbix Agent running"
    echo ""
    echo "Add this host in Zabbix Web UI (http://192.168.10.145:10080):"
    echo "  Host: mac-mini-m4-pro"
    echo "  IP: 192.168.10.145, Port: 10050"
    echo "  Encryption: PSK, Identity: $PSK_IDENTITY"
    echo "  PSK: $PSK_KEY"
    echo "  Template: macOS by Zabbix agent"
else
    echo "❌ Agent not running - check: sudo launchctl list | grep zabbix"
fi
