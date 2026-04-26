# Mac Studio Migration Checklist

**Target:** Move heavy compute workloads from Mac Mini to Mac Studio  
**Keep on Mac Mini:** Dashboard, control panels, monitoring  
**Move to Mac Studio:** Ollama, training, executor workers

---

## PRE-MIGRATION (Mac Mini)

### 1. Test Deploy Scripts
```bash
# Test current deployment on Mac Mini
cd /Users/admin/repos/integrated-ai-platform
./bin/deploy_to_mac_mini.sh

# Verify everything starts
docker ps
curl http://localhost:8080/api/status
```

### 2. Document Current State
```bash
# Capture current configuration
docker ps > /tmp/pre-migration-containers.txt
pip3 freeze > /tmp/pre-migration-python.txt
brew list > /tmp/pre-migration-brew.txt

# Export training data
tar -czf /tmp/training-data-backup.tar.gz artifacts/training_data/

# Backup roadmap state
git add -A
git commit -m "Pre-migration snapshot"
git push origin main
```

### 3. Prepare Data for Transfer
```bash
# Create migration package
mkdir -p /tmp/mac-studio-migration
cp -r artifacts/training_data/ /tmp/mac-studio-migration/
cp -r artifacts/models/ /tmp/mac-studio-migration/
cp docker/.env /tmp/mac-studio-migration/
```

---

## MAC STUDIO SETUP

### 1. Initial Setup
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install essentials
brew install git python@3.11 curl wget

# Install Docker (choose one)
# Option A: Colima (lightweight, current Mac Mini setup)
brew install colima docker docker-compose
colima start --cpu 8 --memory 32 --disk 100

# Option B: Docker Desktop (GUI, easier)
brew install --cask docker
# Open Docker Desktop and configure resources

# Verify Docker
docker ps
```

### 2. Clone Repository
```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/integrated-ai-platform.git
cd integrated-ai-platform

# Or rsync from Mac Mini
rsync -avz --progress admin@mac-mini.local:/Users/admin/repos/integrated-ai-platform/ ~/repos/integrated-ai-platform/
```

### 3. Transfer Migration Data
```bash
# From Mac Mini, push to Mac Studio
rsync -avz --progress /tmp/mac-studio-migration/ admin@mac-studio.local:/tmp/migration/

# On Mac Studio, restore
cd ~/repos/integrated-ai-platform
cp -r /tmp/migration/training_data/ artifacts/
cp -r /tmp/migration/models/ artifacts/
cp /tmp/migration/.env docker/
```

### 4. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt
pip3 install torch torchvision torchaudio  # For training
pip3 install transformers datasets trl peft  # For LoRA
```

### 5. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull qwen2.5-coder:14b
ollama pull llama3.1:8b

# Test Ollama
curl http://localhost:11434/api/tags
```

### 6. Configure Network
```bash
# Get Mac Studio IP
ifconfig | grep "inet "

# Assign static IP (example: 192.168.10.150)
# System Settings → Network → Wi-Fi → Details → TCP/IP
# Configure IPv4: Manually
# IP Address: 192.168.10.150
# Subnet Mask: 255.255.255.0
# Router: 192.168.10.1

# Update /etc/hosts on Mac Mini
ssh admin@mac-mini.local
sudo nano /etc/hosts
# Add: 192.168.10.150 mac-studio.local mac-studio

# Test connectivity
ping mac-studio.local
```

### 7. Deploy Services
```bash
# Run deployment script
cd ~/repos/integrated-ai-platform
./bin/deploy_to_mac_studio.sh

# Verify services
docker ps
curl http://localhost:11434/api/tags  # Ollama
```

---

## INTEGRATION (Mac Mini ↔ Mac Studio)

### 1. Update Dashboard Configuration
On Mac Mini, update dashboard to use Mac Studio Ollama:

```bash
ssh admin@mac-mini.local
cd /Users/admin/repos/integrated-ai-platform

# Update docker/.env
nano docker/.env
# Change:
# OLLAMA_URL=http://mac-studio.local:11434
```

### 2. Test Training Pipeline
On Mac Studio:

```bash
# Test training with small dataset
cd ~/repos/integrated-ai-platform
python3 bin/train_model.py --test-mode

# Check GPU usage (if Mac Studio has GPU)
# System Monitor or: sudo powermetrics --samplers gpu_power -i 1000 -n 1
```

### 3. Configure Executor Split
Update executor config to run on Mac Studio:

```bash
# On Mac Studio, start executor
cd ~/repos/integrated-ai-platform
python3 bin/auto_execute_roadmap.py --max-workers 5 > /tmp/executor.log 2>&1 &

# On Mac Mini, stop local executor
pkill -f auto_execute_roadmap.py
```

### 4. Verify Integration
From Mac Mini dashboard:

```bash
# Test Ollama connection
curl http://mac-studio.local:11434/api/tags

# Test training trigger
# Open dashboard → Training tab → Start Training
# Verify logs on Mac Studio
ssh admin@mac-studio.local tail -f /tmp/training.log

# Test executor
# Dashboard → Executor tab → Start Executor
# Verify on Mac Studio
ssh admin@mac-studio.local tail -f /tmp/executor.log
```

---

## POST-MIGRATION VALIDATION

### 1. Service Health Checks
```bash
# From Mac Mini
curl http://localhost:8080/api/status
curl http://mac-studio.local:11434/api/tags

# From Mac Studio
docker ps
curl http://localhost:11434/api/tags
```

### 2. Performance Benchmarks
```bash
# On Mac Studio, run training benchmark
cd ~/repos/integrated-ai-platform
time python3 bin/train_model.py --test-mode

# Record metrics:
# - Training time
# - GPU utilization (if applicable)
# - Memory usage
# - Disk I/O
```

### 3. Executor Performance
```bash
# Test executor with 5 workers
python3 bin/auto_execute_roadmap.py --max-workers 5 --filter "RM-TESTING-*" --max-items 5

# Measure:
# - Items/hour completion rate
# - Success rate
# - Resource usage
```

---

## ROLLBACK PROCEDURE

If anything goes wrong:

### 1. Stop Mac Studio Services
```bash
ssh admin@mac-studio.local
cd ~/repos/integrated-ai-platform
docker compose down
pkill -f auto_execute_roadmap.py
```

### 2. Restore Mac Mini Configuration
```bash
ssh admin@mac-mini.local
cd /Users/admin/repos/integrated-ai-platform

# Revert .env changes
git checkout docker/.env

# Restart services
docker compose up -d
```

### 3. Verify Rollback
```bash
# Test dashboard
curl http://localhost:8080/api/status

# Test training
curl http://localhost:11434/api/tags
```

---

## OPTIMIZATION (After Migration)

### 1. Tune Executor Workers
Test different worker counts:

```bash
# Test 3, 5, 8 workers
for workers in 3 5 8; do
  echo "Testing  workers..."
  python3 bin/auto_execute_roadmap.py --max-workers  --max-items 10
done
```

### 2. Tune Training Parameters
Optimize for Mac Studio hardware:

```python
# In training config
per_device_train_batch_size = 8  # Increase if GPU memory allows
gradient_accumulation_steps = 2   # Adjust based on batch size
max_seq_length = 1024              # Increase from 512 if memory allows
```

### 3. Monitor Resource Usage
```bash
# Set up monitoring
# Mac Studio: sudo powermetrics --samplers cpu_power,gpu_power -i 5000
# Dashboard: Enable system monitoring tab
```

---

## SUCCESS CRITERIA

### ✅ Migration Complete When:
- [ ] Mac Studio running Ollama
- [ ] Training pipeline working
- [ ] Executor running 5 workers
- [ ] Dashboard on Mac Mini connects to Mac Studio
- [ ] All services healthy (green in dashboard)
- [ ] Performance >= Mac Mini baseline
- [ ] No data loss verified
- [ ] Rollback procedure tested

### 📊 Performance Targets:
- Training: ≥2x faster than Mac Mini
- Executor: 5 parallel workers (vs 1 on Mac Mini)
- Ollama: <1s response time
- Dashboard latency: <100ms

---

**Created:** April 25, 2026  
**Ready for:** Mac Studio arrival (estimated: days away)
