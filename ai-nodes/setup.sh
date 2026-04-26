#!/bin/bash
# AI Node setup script — bare metal Ubuntu 24.04
# Usage: curl -s https://raw.githubusercontent.com/.../setup.sh | bash -s -- i9
# Or:    bash setup.sh i9   /   bash setup.sh i5

NODE_TYPE="${1:-}"
if [[ "$NODE_TYPE" != "i9" && "$NODE_TYPE" != "i5" ]]; then
  echo "Usage: $0 [i9|i5]"
  exit 1
fi

set -e

TAILSCALE_KEY="${TAILSCALE_AUTH_KEY:-}"  # Set via env before running

echo "=== AI Node setup: ai-node-${NODE_TYPE} ==="

# 1. System update
apt-get update && apt-get upgrade -y
apt-get install -y curl wget git htop nvtop intel-gpu-tools

# 2. Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
if [[ -n "$TAILSCALE_KEY" ]]; then
  tailscale up --authkey "$TAILSCALE_KEY" --hostname "ai-node-${NODE_TYPE}"
else
  echo "!! Set TAILSCALE_AUTH_KEY env var or run: tailscale up --authkey <key> --hostname ai-node-${NODE_TYPE}"
fi

# 3. Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama for bare metal performance
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_NUM_PARALLEL=4"
EOF

systemctl daemon-reload
systemctl enable ollama
systemctl restart ollama

# 4. Intel Arc iGPU support voor Ollama (optioneel, MS-01 heeft Arc iGPU)
apt-get install -y gpg
wget -qO - https://repositories.intel.com/gpu/intel-graphics.key | gpg --dearmor -o /usr/share/keyrings/intel-graphics.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu noble unified" \
  > /etc/apt/sources.list.d/intel-gpu-noble.list
apt-get update
apt-get install -y intel-opencl-icd intel-level-zero-gpu level-zero

# Add ollama user to render/video group for GPU access
usermod -aG render ollama 2>/dev/null || true
usermod -aG video ollama 2>/dev/null || true
systemctl restart ollama

echo "=== Setup ai-node-${NODE_TYPE} voltooid ==="
echo "Volgende stappen:"
echo "  1. Verifieer Tailscale: tailscale status"
echo "  2. Trek modellen: ollama pull qwen2.5:7b"
echo "  3. Test: curl http://localhost:11434/api/version"
