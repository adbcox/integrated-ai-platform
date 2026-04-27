#!/bin/bash
# Mac Mini Zabbix Agent Installer
# Run with: sudo bash install-mac-agent.sh
# Uses zabbix_agentd (agent1) — no ARM64 package exists for agent2 on macOS

set -e

PSK_KEY="1939b436368d7c971567d07aef8ddb94027860315a0b4e7cbb3397974e3e5c3d"
PSK_IDENTITY="mac-mini-m4-pro-psk"
PKG="$HOME/Downloads/zabbix_agent-7.4.9-macos-arm64-openssl.pkg"

if [ ! -f "$PKG" ]; then
  echo "Downloading Zabbix agent..."
  curl -L --max-time 120 \
    "https://cdn.zabbix.com/zabbix/binaries/stable/7.4/7.4.9/zabbix_agent-7.4.9-macos-arm64-openssl.pkg" \
    -o "$PKG"
fi

echo "Installing Zabbix Agent 7.4.9..."
installer -pkg "$PKG" -target /

echo "Writing PSK file..."
mkdir -p /usr/local/etc/zabbix
printf '%s' "$PSK_KEY" | tee /usr/local/etc/zabbix/agent.psk > /dev/null
chmod 600 /usr/local/etc/zabbix/agent.psk
chown root:wheel /usr/local/etc/zabbix/agent.psk

echo "Writing agent config..."
tee /usr/local/etc/zabbix/zabbix_agentd.conf > /dev/null << 'EOF'
Server=192.168.10.145
ServerActive=192.168.10.145
Hostname=mac-mini-m4-pro
ListenPort=10050
TLSConnect=psk
TLSAccept=psk
TLSPSKIdentity=mac-mini-m4-pro-psk
TLSPSKFile=/usr/local/etc/zabbix/agent.psk
LogFile=/var/log/zabbix/zabbix_agentd.log
LogFileSize=10
DebugLevel=3
EOF

mkdir -p /var/log/zabbix

echo "Starting agent..."
launchctl unload /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist 2>/dev/null || true
launchctl load /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist

sleep 2
if ps aux | grep -v grep | grep -q zabbix_agentd; then
    echo ""
    echo "✅ Zabbix Agent running"
    echo "   Host: mac-mini-m4-pro | PSK identity: $PSK_IDENTITY"
    echo "   PSK already configured in Zabbix (hostid=10782)"
else
    echo "❌ Agent not running - check: sudo launchctl list | grep zabbix"
    exit 1
fi
