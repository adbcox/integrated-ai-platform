# Mac Studio — AI Compute Node

## Status: PENDING ARRIVAL

This system is documented ahead of deployment. Configuration will be finalized
when the hardware arrives.

## Expected Hardware

| Spec | Value |
|------|-------|
| Model | Mac Studio (2025) |
| Chip | Apple M4 Max (expected) |
| RAM | **96 GB unified memory** |
| IP | 192.168.10.202 (reserved in DHCP) |
| Hostname | mac-studio.local (planned) |
| Role | **AI compute: Ollama inference + LoRA training** |

## Why a Second Machine?

The Mac Mini (48GB) is sufficient for orchestration but cannot comfortably run:
- Large Ollama models (e.g., 70B parameter) — need 40+ GB just for the model
- LoRA fine-tuning of Qwen2.5-Coder-7B — need GPU memory for torch + peft
- Concurrent inference under load — mini gets saturated with 14B model + platform

The Mac Studio offloads all GPU-intensive work, keeping the Mini responsive.

## Planned Services

| Service | Port | Purpose |
|---------|------|---------|
| Ollama | 11434 | Local LLM inference (qwen2.5-coder:14b, :32b, :70b) |
| node-exporter | 9100 | System metrics → vmagent on Mini |
| LoRA training loop | — | `~/training-env` venv, fine-tuning pipeline |

## Deployment Runbook (when hardware arrives)

```bash
# 1. Install Homebrew + system deps
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Ollama
brew install ollama

# 3. Pull models
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b   # 96GB allows this comfortably

# 4. Set Ollama to listen on all interfaces (for Mini to reach it)
# Edit /etc/launchd.conf or create launchd plist:
# OLLAMA_HOST=0.0.0.0:11434

# 5. Install node-exporter via Docker
docker run -d \
  --name node-exporter \
  --net=host \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  prom/node-exporter:v1.7.0

# 6. Clone repo
git clone https://github.com/adbcox/integrated-ai-platform.git ~/repos/integrated-ai-platform

# 7. Set up training environment
python3.12 -m venv ~/training-env
source ~/training-env/bin/activate
pip install torch torchvision peft transformers accelerate

# 8. Point vmagent on Mini to scrape Studio
# Add to docker/vmagent-config/scrape.yml:
#   - job_name: mac_studio_node
#     static_configs:
#       - targets: ['192.168.10.202:9100']
#   - job_name: mac_studio_ollama
#     static_configs:
#       - targets: ['192.168.10.202:11434']
#     metrics_path: /metrics
```

## Integration with Mac Mini

Once running, the Mini's `task_decomposer.py` will switch from localhost to
the Studio for Ollama calls:

```bash
# Set in docker/.env on Mac Mini:
OLLAMA_API_BASE=http://192.168.10.202:11434
```

And update vmagent scrape config to include the Studio node.

## LoRA Training Migration

The training pipeline in `framework/model_trainer.py` is designed to run on
the Studio. After cloning the repo there:

```bash
# On Mac Studio, from repo root:
python3 bin/run_training_cycle.py \
  --model qwen2.5-coder:14b \
  --data-source artifacts/learning_events/ \
  --output artifacts/lora_adapter/
```

The resulting GGUF adapter gets loaded into Ollama:
```bash
ollama create qwen25-finetuned -f artifacts/lora_adapter/Modelfile
```
