# Home Network Transition: Mac Studio LAN Access

**Date Created:** 2026-05-09
**Purpose:** Switch LiteLLM proxy tier-2 routing between stunt-double (Singapore/off-LAN) and Mac Studio (home LAN) configurations
**Audience:** Operator (when transitioning between home network and remote locations)

## Overview

The LiteLLM proxy is configured to support two tier-2 deployment modes:

1. **Stunt-Double Mode (Current: Singapore)** — Simulated tier-2 on localhost:11435
   - Use when: Off-network, cannot access Mac Studio via LAN
   - Configuration: `api_base: http://127.0.0.1:11435`
   - Fallback behavior: Fires immediately if stunt-double unreachable

2. **Home LAN Mode** — Direct access to Mac Studio on home network
   - Use when: On home network with Mac Studio available
   - Configuration: `api_base: http://192.168.10.142:11434`
   - Fallback behavior: Fires if Mac Studio is off or unreachable

## Switching to Home LAN Mode

### Prerequisites

- ✓ Mac Studio Ollama running (`ollama serve`)
- ✓ Network connectivity to 192.168.10.142 on port 11434
- ✓ Verify connectivity: `curl http://192.168.10.142:11434/api/tags`

### Steps

**1. Update LiteLLM Configuration**

Edit `~/local-ai-workstation/configs/litellm/config.yaml`:

```yaml
- model_name: qwen3-coder-30b
  litellm_params:
    model: ollama/qwen3-coder:30b-coding
    api_base: http://192.168.10.142:11434    # Switch back to home LAN
    timeout: 5
    stream_timeout: 5
```

**2. Reload LiteLLM Proxy**

```bash
launchctl unload ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 1
launchctl load ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 2
```

**3. Verify Connectivity**

```bash
curl -H "Authorization: Bearer sk-local-only-not-secret" \
  http://localhost:4000/v1/models | jq '.data[] | .id'
```

Expected output:
```
"qwen2.5-coder"
"qwen3-coder-30b"
```

**4. Test Routing**

```bash
time curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-local-only-not-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder-30b",
    "messages": [{"role": "user", "content": "respond with HOME_LAN_OK"}],
    "max_tokens": 20
  }' | jq '.choices[0].message.content'
```

Expected response: `"HOME_LAN_OK"` (from Mac Studio)

---

## Switching Back to Stunt-Double Mode

### Prerequisites

- ✓ Stunt-Double Ollama running on port 11435
  - Verify: `OLLAMA_HOST=127.0.0.1:11435 ollama ps`
- ✓ Model loaded: `OLLAMA_HOST=127.0.0.1:11435 ollama list`

### Steps

**1. Update LiteLLM Configuration**

Edit `~/local-ai-workstation/configs/litellm/config.yaml`:

```yaml
- model_name: qwen3-coder-30b
  litellm_params:
    model: ollama/qwen3-coder:30b-coding
    api_base: http://127.0.0.1:11435         # Switch to stunt-double
    timeout: 5
    stream_timeout: 5
```

**2. Reload LiteLLM Proxy**

```bash
launchctl unload ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 1
launchctl load ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 2
```

**3. Verify Connectivity**

```bash
curl -H "Authorization: Bearer sk-local-only-not-secret" \
  http://localhost:4000/v1/models | jq '.data[] | .id'
```

**4. Test Routing**

```bash
time curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-local-only-not-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder-30b",
    "messages": [{"role": "user", "content": "respond with STUNT_DOUBLE_OK"}],
    "max_tokens": 20
  }' | jq '.choices[0].message.content'
```

Expected response: `"STUNT_DOUBLE_OK"` (from stunt-double on localhost:11435)

---

## Troubleshooting

### LiteLLM Not Responding After Reload

```bash
# Check service status
launchctl list | grep litellm

# View recent logs
tail -50 ~/local-ai-workstation/logs/litellm.err
```

If service won't load, check for configuration syntax errors:
```bash
cat ~/local-ai-workstation/configs/litellm/config.yaml
```

### Tier-2 Connectivity Issues

**For Home LAN:**
```bash
# Test Mac Studio connectivity
ping -c 1 192.168.10.142
curl http://192.168.10.142:11434/api/tags
```

**For Stunt-Double:**
```bash
# Test stunt-double is running
OLLAMA_HOST=127.0.0.1:11435 /opt/homebrew/bin/ollama ps
curl http://127.0.0.1:11435/api/tags
```

### Slow Fallback Response

If fallback is taking >10 seconds, verify tier-2 timeout in config is set to 5s (not higher):

```yaml
- model_name: qwen3-coder-30b
  litellm_params:
    timeout: 5           # Should be 5, not 30
    stream_timeout: 5    # Should be 5, not 30
```

Then reload LiteLLM.

---

## Operational Notes

- **Auto-Fallback Behavior:** When tier-2 (qwen3-coder-30b) times out or is unreachable, router immediately falls back to tier-1 (qwen2.5-coder on localhost:11434). Fallback response time is <1 second.

- **Configuration Persistence:** Changes to `litellm/config.yaml` take effect after `launchctl` reload. Changes are NOT automatically applied.

- **Agent Tool Compatibility:** All agent tools (OpenCode, Goose, Aider, Continue) route transparently through LiteLLM proxy. No per-tool configuration changes needed when switching modes — proxy handles routing.

- **Model Availability:**
  - Tier-1 (local): `qwen2.5-coder:7b` (always available)
  - Tier-2 (home LAN): `qwen3-coder:30b-coding` (home network only)
  - Tier-2 (stunt-double): `qwen2.5-coder:7b` (for Singapore testing)

---

## Quick Transition Scripts

### Activate Home LAN (Mac Studio Available)

```bash
sed -i '' 's|api_base: http://127.0.0.1:11435|api_base: http://192.168.10.142:11434|' \
  ~/local-ai-workstation/configs/litellm/config.yaml

launchctl unload ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 1
launchctl load ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 2

echo "Home LAN activated. Testing..."
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer sk-local-only-not-secret" | jq '.data | length'
```

### Activate Stunt-Double (Off-Network)

```bash
sed -i '' 's|api_base: http://192.168.10.142:11434|api_base: http://127.0.0.1:11435|' \
  ~/local-ai-workstation/configs/litellm/config.yaml

launchctl unload ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 1
launchctl load ~/Library/LaunchAgents/com.adriancox.litellm.plist
sleep 2

echo "Stunt-Double activated. Testing..."
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer sk-local-only-not-secret" | jq '.data | length'
```
