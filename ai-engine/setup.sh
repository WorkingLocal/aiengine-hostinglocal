#!/usr/bin/env bash
# AI Engine — setup script voor de Blog Convertor engine
# (Ubuntu 24.04 VM op Windows Server 2025 Hyper-V)
#
# Installeert en configureert:
#   - Ollama (LLM inference)
#   - LiteLLM als Docker container (OpenAI-compatibele proxy, poort 4000)
#   - Stats Service (poort 11435 — RAM/CPU/modellen voor Blog Convertor UI)
#   - Image Gen Service (poort 11436 — SDXL lokaal of Replicate API)
#
# Vereisten:
#   - Ubuntu 24.04 LTS
#   - Tailscale geïnstalleerd en verbonden (IP: 100.80.180.55)
#   - Docker geïnstalleerd
#   - Gebruiker: ailocal
#
# Gebruik:
#   sudo bash ai-engine/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME=/home/ailocal

echo "=== AI Engine Setup — Blog Convertor ==="

# ── Ollama ──────────────────────────────────────────────────────────────────
echo ""
echo "==> Ollama installeren..."
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "    Ollama al geïnstalleerd: $(ollama --version)"
fi

# ── LiteLLM ─────────────────────────────────────────────────────────────────
echo ""
echo "==> LiteLLM Docker container configureren..."
mkdir -p "$USER_HOME/litellm"
cp "$SCRIPT_DIR/litellm/config.yaml" "$USER_HOME/litellm/config.yaml"
chown -R ailocal:ailocal "$USER_HOME/litellm"

# Stop eventuele bestaande container
docker stop litellm 2>/dev/null || true
docker rm litellm 2>/dev/null || true

docker run -d \
  --name litellm \
  --restart unless-stopped \
  --add-host host.docker.internal:host-gateway \
  -p 4000:4000 \
  -v "$USER_HOME/litellm/config.yaml:/app/config.yaml:ro" \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml

echo "    LiteLLM actief op poort 4000"

# ── Stats Service ────────────────────────────────────────────────────────────
echo ""
echo "==> Stats Service installeren (poort 11435)..."
cp "$SCRIPT_DIR/stats-server.py" "$USER_HOME/stats-server.py"
chown ailocal:ailocal "$USER_HOME/stats-server.py"
cp "$SCRIPT_DIR/stats-server.service" /etc/systemd/system/ai-stats.service
systemctl daemon-reload
systemctl enable ai-stats
systemctl restart ai-stats
echo "    Stats Service actief op poort 11435"

# ── Image Gen Service ────────────────────────────────────────────────────────
echo ""
echo "==> Image Gen Service installeren (poort 11436)..."
mkdir -p "$USER_HOME/image-gen"
cp "$SCRIPT_DIR/image-gen/server.py" "$USER_HOME/image-gen/server.py"
chown -R ailocal:ailocal "$USER_HOME/image-gen"

# Python venv aanmaken (PEP 668 — geen system pip)
if [ ! -d "$USER_HOME/image-gen/venv" ]; then
  apt-get install -y python3.12-venv
  sudo -u ailocal python3 -m venv "$USER_HOME/image-gen/venv"
fi

# Afhankelijkheden installeren
sudo -u ailocal "$USER_HOME/image-gen/venv/bin/pip" install --quiet \
  torch --index-url https://download.pytorch.org/whl/cpu
sudo -u ailocal "$USER_HOME/image-gen/venv/bin/pip" install --quiet \
  diffusers transformers accelerate

cp "$SCRIPT_DIR/image-gen/image-gen.service" /etc/systemd/system/ai-image-gen.service
systemctl daemon-reload
systemctl enable ai-image-gen
systemctl restart ai-image-gen
echo "    Image Gen Service actief op poort 11436"
echo "    Opmerking: SDXL-model wordt bij eerste aanvraag gedownload (~6 GB)"

# ── Modellen downloaden ──────────────────────────────────────────────────────
echo ""
echo "==> Ollama modellen downloaden (voer manueel uit bij voldoende resources):"
echo ""
echo "    ollama pull qwen2.5:72b     # ~47 GB — primair conversiemodel"
echo "    ollama pull qwen2.5:32b     # ~20 GB"
echo "    ollama pull qwen2.5:7b      # ~4.7 GB"
echo "    ollama pull llama3.3:70b    # ~43 GB"
echo "    ollama pull qwen2-vl:7b     # ~5.5 GB — vision model voor afbeeldingsbeschrijving"
echo ""

echo "=== AI Engine Setup voltooid ==="
echo ""
echo "Services:"
echo "  Ollama:    http://localhost:11434"
echo "  LiteLLM:   http://localhost:4000"
echo "  Stats:     http://localhost:11435/api/stats"
echo "  Image Gen: http://localhost:11436/generate"
echo ""
echo "  Via Tailscale bereikbaar op 100.80.180.55"
