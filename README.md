# AI Engine — hostinglocal

Centrale AI Engine voor Working Local toepassingen: LLM-inferentie, beeldgeneratie en gerelateerde AI-services.

**3-node AI cluster (volledig operationeel ✅):**

| Node | Hardware | RAM | Tailscale IP | Rol |
|---|---|---|---|---|
| `ai-engine` | Hyper-V VM op Windows Server | 12 GB | 100.80.180.55 | LiteLLM proxy + vision |
| `ai-node-i9` | Minisforum MS-01 i9-13900H bare metal | 64 GB | 100.126.121.11 | Primaire inference (72B modellen) |
| `ai-node-i5` | Minisforum MS-01 i5 bare metal | 32 GB | 100.78.175.49 | Lichte inference (7B modellen) |

## Publiek AI-endpoint

```
https://ai.hostinglocal.be
```

OpenAI-compatibele API via LiteLLM (Cloudflare HOMELAB tunnel → ai-engine :4000).

Nieuwe key aanmaken voor een vriend:
```bash
curl -X POST https://ai.hostinglocal.be/key/generate \
  -H "Authorization: Bearer <master_key>" \
  -H "Content-Type: application/json" \
  -d '{"key_alias": "naam-vriend"}'
```

## Huidige toepassingen

| Toepassing | Services gebruikt |
|---|---|
| Blog Convertor | LiteLLM (tekstconversie), Stats Service (UI monitoring), Image Gen (afbeeldingen), Ollama Vision |
| Vrienden | LiteLLM API via https://ai.hostinglocal.be |
| Continue (VSCode) | LiteLLM via https://ai.hostinglocal.be/v1 — lokale AI code-assistent (Qwen2.5-Coder) |

## Hardware

### ai-engine (Hyper-V VM) — live ✅

| Parameter | Waarde |
|---|---|
| Host OS | Windows Server 2025 |
| Hypervisor | Hyper-V |
| VM naam | ai-engine |
| VM OS | Ubuntu 24.04 LTS |
| vCPUs | 20 |
| RAM | 96 GB |
| Gebruiker | `ailocal` |
| Tailscale IP | `100.80.180.55` |

### ai-node-i9 (bare metal) — live ✅

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 9 (i9-13900H) |
| RAM | 64 GB |
| Opslag | 4 TB + 2 TB + 1 TB NVMe |
| iGPU | Intel Arc (drivers geïnstalleerd) |
| Netwerk IP | 192.168.111.31 (10GbE SFP+, statisch) |
| Tailscale IP | 100.126.121.11 |
| Hostname | ai-node-i9 |
| OS | Ubuntu 24.04 LTS |

### ai-node-i5 (bare metal) — live ✅

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 5 (i5) |
| RAM | 32 GB |
| iGPU | Intel Arc (drivers geïnstalleerd) |
| Netwerk IP | 192.168.111.32 (10GbE SFP+, statisch) |
| Tailscale IP | 100.78.175.49 |
| Hostname | ai-node-i5 |
| OS | Ubuntu 24.04 LTS |

## Services

### ai-engine VM

| Service | Poort | Type | Omschrijving |
|---|---|---|---|
| Ollama | 11434 | systemd | LLM inference engine (fallback) |
| LiteLLM | 4000 | Docker Compose | OpenAI-compatibele proxy — centrale router |
| LiteLLM DB | — | Docker (postgres:16) | Persistent key management |
| Stats Service | 11435 | systemd (`ai-stats`) | RAM/CPU/model monitoring |
| Image Gen Service | 11436 | systemd (`ai-image-gen`) | Afbeeldingen genereren (SDXL of Replicate) |
| node_exporter | 9100 | systemd | Prometheus metrics |

### ai-node-i9

| Service | Poort | Type | Status |
|---|---|---|---|
| Ollama | 11434 | systemd | ✅ actief |
| node_exporter | 9100 | systemd | ✅ actief |

> **ZFS ARC limiet:** ai-node-i9 exporteert NVMe via ZFS/NFS (muziek + fotos). ZFS ARC beperkt tot 10GB zodat qwen2.5:72b (48.5GB) kan laden. Persistent via `/etc/modprobe.d/zfs.conf`.

### ai-node-i5

| Service | Poort | Type | Status |
|---|---|---|---|
| Ollama | 11434 | systemd | ✅ actief |
| node_exporter | 9100 | systemd | ✅ actief |
| immich-machine-learning | 3003 | Docker | ✅ actief (OpenVINO) |

## LiteLLM model routing

| Model | Primaire backend | Fallback | Grootte |
|---|---|---|---|
| `qwen2.5-72b` | ai-node-i9 (snelste CPU) | — | ~47 GB |
| `qwen2.5-7b` | ai-node-i5 | — | ~4.7 GB |
| `qwen2.5vl-7b` | ai-engine VM | — | ~5.5 GB (vision) |
| `standaard` | ai-node-i9 | — | alias → 72b |
| `qwen2.5-coder-32b` | ai-node-i9 | — | ~20 GB |
| `qwen2.5-coder-7b` | ai-node-i5 | — | ~4.7 GB |
| `qwen2.5-coder-1.5b` | ai-node-i5 | — | ~1 GB |

## Repository structuur

```
aiengine-hostinglocal/
├── ai-engine/
│   ├── setup.sh                # Volledig installatiescript (ai-engine VM)
│   ├── stats-server.py         # Stats Service (poort 11435)
│   ├── stats-server.service    # systemd unit voor stats-server
│   ├── litellm/
│   │   ├── config.yaml         # LiteLLM configuratie (multi-node routing)
│   │   └── docker-compose.yml  # LiteLLM + PostgreSQL key mgmt DB
│   └── image-gen/
│       ├── server.py           # Image Gen Service (poort 11436)
│       └── image-gen.service   # systemd unit voor image-gen
└── ai-nodes/
    ├── setup.sh                # Installatiescript voor beide nodes (i9/i5)
    ├── ai-node-i9/
    │   └── node.md             # Hardware specs + installatiestatus i9
    └── ai-node-i5/
        └── node.md             # Hardware specs + installatiestatus i5
```

## Installatie

### ai-engine VM

```bash
sudo bash ai-engine/setup.sh
```

### ai-nodes (i9 / i5)

```bash
TAILSCALE_AUTH_KEY=<key> bash ai-nodes/setup.sh i9   # of i5
```

Het script installeert automatisch:
- Tailscale
- Ollama (OLLAMA_HOST=0.0.0.0, OLLAMA_NUM_PARALLEL=4)
- Intel Arc iGPU drivers (intel-opencl-icd, level-zero)
- node_exporter (Prometheus monitoring, poort 9100)

## Ollama configuratie

### ai-engine VM (HyperV)

`/etc/systemd/system/ollama.service.d/override.conf`

| Variabele | Waarde | Waarom |
|---|---|---|
| `OLLAMA_HOST` | `0.0.0.0` | Bereikbaar vanuit Docker (LiteLLM) en netwerk |
| `OLLAMA_NUM_THREAD` | `20` | Alle vCPUs gebruiken (standaard: alleen fysieke cores = 50% CPU op HyperV) |
| `OLLAMA_NUM_PARALLEL` | `2` | Twee gelijktijdige inference requests op hetzelfde model |

### ai-nodes (bare metal)

| Variabele | Waarde |
|---|---|
| `OLLAMA_HOST` | `0.0.0.0` |
| `OLLAMA_NUM_PARALLEL` | `4` |

> Geen `OLLAMA_NUM_THREAD` nodig op bare metal — Ollama detecteert alle cores automatisch correct.

Na aanpassen: `systemctl daemon-reload && systemctl restart ollama`

## Ollama modellen

```bash
# ai-node-i9 (64 GB RAM) — primaire node
ollama pull qwen2.5:72b           # ~47 GB — primair conversiemodel
ollama pull qwen2.5-coder:32b     # ~20 GB — code-assistent (Continue/VSCode)

# ai-node-i5 (32 GB RAM) — lichte inference
ollama pull qwen2.5:7b            # ~4.7 GB
ollama pull qwen2.5-coder:7b      # ~4.7 GB — code-assistent
ollama pull qwen2.5-coder:1.5b    # ~1 GB — autocomplete (Continue/VSCode)

# ai-engine VM (96 GB RAM) — fallback + extra modellen
ollama pull qwen2.5:72b     # fallback voor i9
ollama pull qwen2.5:32b     # ~20 GB
ollama pull qwen2.5:7b      # fallback voor i5
ollama pull llama3.3:70b    # ~43 GB
ollama pull qwen2.5vl:7b    # ~5.5 GB — vision model
```

| Ollama model | LiteLLM naam | Grootte | Primaire node |
|---|---|---|---|
| `qwen2.5:72b` | `qwen2.5-72b` | ~47 GB | ai-node-i9 |
| `qwen2.5:32b` | `qwen2.5-32b` | ~20 GB | ai-engine VM |
| `qwen2.5:7b` | `qwen2.5-7b` | ~4.7 GB | ai-node-i5 |
| `llama3.3:70b` | `llama3.3-70b` | ~43 GB | ai-engine VM |
| `qwen2.5vl:7b` | `qwen2.5vl-7b` | ~5.5 GB | ai-engine VM (vision) |
| `qwen2.5-coder:32b` | `qwen2.5-coder-32b` | ~20 GB | ai-node-i9 |
| `qwen2.5-coder:7b` | `qwen2.5-coder-7b` | ~4.7 GB | ai-node-i5 |
| `qwen2.5-coder:1.5b` | `qwen2.5-coder-1.5b` | ~1 GB | ai-node-i5 |

> **Let op naamgeving:** Ollama gebruikt `qwen2.5vl:7b` (met punt), LiteLLM exposeert dit als `qwen2.5vl-7b` (met koppelteken).

## Monitoring

Alle nodes worden gemonitord via Prometheus (metrics-workinglocal repo, Grafana op https://metrics.workinglocal.be):

| Node | Tailscale IP | Poort |
|---|---|---|
| ai-engine | 100.80.180.55 | 9100 |
| ai-node-i9 | 100.126.121.11 | 9100 |
| ai-node-i5 | 100.78.175.49 | 9100 |

## Afbeeldingen genereren

**Lokaal (diffusers, CPU):**

| Model | `image_model` waarde | Stappen | Resolutie |
|---|---|---|---|
| Stable Diffusion XL 1.0 | `sdxl` | 20 | 1024×1024 |
| SDXL Turbo | `sdxl-turbo` | 4 | 1024×1024 |
| Stable Diffusion 1.5 | `sd15` | 20 | max 512×512 |

**Replicate API (cloud):** `sdxl`, `flux-schnell`, `flux-dev`

## Beheer

```bash
# LiteLLM (op ai-engine VM)
cd /home/ailocal/litellm
docker compose logs litellm -f
docker compose restart litellm

# Nieuwe API key aanmaken voor vriend
curl -X POST https://ai.hostinglocal.be/key/generate \
  -H "Authorization: Bearer HostingLocal2024" \
  -H "Content-Type: application/json" \
  -d '{"key_alias": "naam-vriend"}'

# Stats Service
systemctl status ai-stats
journalctl -u ai-stats -f

# Image Gen Service
systemctl status ai-image-gen
journalctl -u ai-image-gen -f

# Ollama modellen
ollama list          # geïnstalleerde modellen
ollama ps            # actief geladen modellen

# LiteLLM config aanpassen en herladen
nano /home/ailocal/litellm/config.yaml
docker compose restart litellm
```

## Continue — VSCode AI code-assistent

Continue (v1.2.22) is geconfigureerd in VSCode op de developer laptop en verbindt via LiteLLM met de Qwen2.5-Coder modellen.

**Config:** `C:\Users\Lenovo\.continue\config.yaml`

| Model | Rol | LiteLLM naam |
|---|---|---|
| Qwen2.5-Coder 32B | chat + edit | `qwen2.5-coder-32b` |
| Qwen2.5-Coder 7B | chat (snel) | `qwen2.5-coder-7b` |
| Qwen2.5-Coder 1.5B | autocomplete | `qwen2.5-coder-1.5b` |

**Credentials:** LiteLLM Master Key (`HostingLocal2024`) → opgeslagen in Vaultwarden als "LiteLLM Master Key"

**API endpoint:** `https://ai.hostinglocal.be/v1` (Cloudflare tunnel) of intern `http://100.80.180.55:4000`

## Gerelateerde repositories

| Repo | Inhoud |
|---|---|
| [n8n-workinglocal](https://github.com/WorkingLocal/n8n-workinglocal) | n8n workflows (incl. Blog Convertor) |
| [vps-workinglocal](https://github.com/WorkingLocal/vps-workinglocal) | Blog Convertor UI (Node.js, VPS poort 3456) |
| [metrics-workinglocal](https://github.com/WorkingLocal/metrics-workinglocal) | Prometheus + Grafana monitoring stack |
| [onpremise-workinglocal](https://github.com/WorkingLocal/onpremise-workinglocal) | On-premise Working Local server |
