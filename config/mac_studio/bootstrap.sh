#!/usr/bin/env bash
# Mac Studio bootstrap — run once after first login
# Hardware: Apple M3, 96 GB RAM, target IP 192.168.10.202
# Sets up Ollama, aider worker env, and platform connectivity
set -euo pipefail

PLATFORM_URL="http://192.168.10.113:8080"   # Mac Mini M5 orchestrator
OLLAMA_PORT=11434

echo "=== Mac Studio Bootstrap (Apple M3 / 96 GB) ==="

# 1. Homebrew
if ! command -v brew &>/dev/null; then
  echo "[brew] Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "[brew] Already installed"
fi

# 2. Ollama
if ! command -v ollama &>/dev/null; then
  echo "[ollama] Installing..."
  brew install ollama
else
  echo "[ollama] Already installed"
fi

# 3. Configure Ollama to listen on LAN
PLIST=~/Library/LaunchAgents/com.ollama.server.plist
if [ ! -f "$PLIST" ]; then
  echo "[ollama] Writing LaunchAgent plist..."
  cat > "$PLIST" <<'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>       <string>com.ollama.server</string>
  <key>ProgramArguments</key>
  <array><string>/opt/homebrew/bin/ollama</string><string>serve</string></array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>OLLAMA_HOST</key>    <string>0.0.0.0</string>
    <key>OLLAMA_ORIGINS</key> <string>*</string>
  </dict>
  <key>RunAtLoad</key>    <true/>
  <key>KeepAlive</key>    <true/>
  <key>StandardOutPath</key>  <string>/tmp/ollama.out.log</string>
  <key>StandardErrorPath</key><string>/tmp/ollama.err.log</string>
</dict>
</plist>
PLIST_EOF
  launchctl load "$PLIST"
  echo "[ollama] LaunchAgent loaded"
else
  echo "[ollama] LaunchAgent already exists"
fi

# 4. Pull default models
echo "[ollama] Pulling models (this takes a while)..."
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b

# 5. uv (for aider)
if ! command -v uv &>/dev/null; then
  echo "[uv] Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source ~/.cargo/env 2>/dev/null || true
  export PATH="$HOME/.cargo/bin:$PATH"
else
  echo "[uv] Already installed"
fi

# 6. aider
if ! command -v aider &>/dev/null; then
  echo "[aider] Installing via uv..."
  uv tool install aider-chat
else
  echo "[aider] Already installed"
fi

# 7. Clone platform repo
REPO_DIR=~/repos/integrated-ai-platform
if [ ! -d "$REPO_DIR" ]; then
  echo "[repo] Cloning integrated-ai-platform..."
  mkdir -p ~/repos
  git clone git@github.com:$(git -C . remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||') "$REPO_DIR" 2>/dev/null \
    || echo "[repo] WARN: clone failed — set up SSH key and retry"
else
  echo "[repo] Already cloned at $REPO_DIR"
fi

# 8. Write aider worker env
ENV_FILE=~/.aider_worker.env
cat > "$ENV_FILE" <<ENV_EOF
OLLAMA_HOST=0.0.0.0
OLLAMA_API_BASE=http://localhost:${OLLAMA_PORT}
AIDER_WORKER_MODEL=ollama/qwen2.5-coder:32b
PLATFORM_API_BASE=${PLATFORM_URL}
ENV_EOF
echo "[env] Wrote $ENV_FILE"

# 9. Verify connectivity back to Mac Mini
echo "[check] Pinging platform at $PLATFORM_URL (Mac Mini M5)..."
if curl -sf "$PLATFORM_URL/api/status" &>/dev/null; then
  echo "[check] Platform reachable ✓"
else
  echo "[check] WARN: platform unreachable — is Mac Mini M5 (192.168.10.113) dashboard running?"
fi

echo ""
echo "=== Bootstrap complete ==="
echo "Ollama LAN endpoint: http://\$(ipconfig getifaddr en0):${OLLAMA_PORT}"
echo "Next steps:"
echo "  1. Add DHCP reservation for this MAC at 192.168.10.202 in OPNsense"
echo "  2. Update config/mac_studio/system_profile.yaml with mac_address"
echo "  3. Update platform aider config to point at Mac Studio Ollama"
