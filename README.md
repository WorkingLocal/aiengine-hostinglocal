# AI Engine — hostinglocal

Centrale AI Engine voor Working Local toepassingen: LLM-inferentie, beeldgeneratie en gerelateerde AI-services.

Draait als Ubuntu 24.04 VM op een Windows Server 2025 host (Hyper-V), bereikbaar via Tailscale op `100.80.180.55`.

## Huidige toepassingen

| Toepassing | Services gebruikt |
|---|---|
| Blog Convertor | LiteLLM (tekstconversie), Stats Service (UI monitoring), Image Gen (afbeeldingen), Ollama Vision |

## Hardware

| Parameter | Waarde |
|---|---|
| Host OS | Windows Server 2025 |
| Hypervisor | Hyper-V |
| VM naam | ai-engine |
| VM OS | Ubuntu 24.04 LTS |
| vCPUs | 20 |
| RAM | 94 GB |
| Gebruiker | `ailocal` |
| Tailscale IP | `100.80.180.55` |

## Services

| Service | Poort | Type | Omschrijving |
|---|---|---|---|
| Ollama | 11434 | systemd | LLM inference engine |
| LiteLLM | 4000 | Docker container | OpenAI-compatibele proxy naar Ollama |
| Stats Service | 11435 | systemd (`ai-stats`) | RAM/CPU/model monitoring |
| Image Gen Service | 11436 | systemd (`ai-image-gen`) | Afbeeldingen genereren (SDXL of Replicate) |

## Repository structuur

```
aiengine-hostinglocal/
└── ai-engine/
    ├── setup.sh                # Volledig installatiescript
    ├── stats-server.py         # Stats Service (poort 11435)
    ├── stats-server.service    # systemd unit voor stats-server
    ├── litellm/
    │   └── config.yaml         # LiteLLM configuratie (modellen + timeout)
    └── image-gen/
        ├── server.py           # Image Gen Service (poort 11436)
        └── image-gen.service   # systemd unit voor image-gen
```

## Installatie

```bash
# Op de AI Engine VM (als root):
sudo bash ai-engine/setup.sh
```

Het script installeert automatisch:
- Ollama
- LiteLLM Docker container
- Stats Service (systemd)
- Image Gen Service (Python venv + systemd)

## Ollama configuratie

De Ollama service wordt geconfigureerd via een systemd override:

```
/etc/systemd/system/ollama.service.d/override.conf
```

| Variabele | Waarde | Waarom |
|---|---|---|
| `OLLAMA_HOST` | `0.0.0.0` | Bereikbaar vanuit Docker (LiteLLM) en netwerk |
| `OLLAMA_NUM_THREAD` | `20` | Alle vCPUs gebruiken (standaard: alleen fysieke cores = 50% CPU op HyperV) |
| `OLLAMA_NUM_PARALLEL` | `2` | Twee gelijktijdige inference requests op hetzelfde geladen model |

Na aanpassen: `systemctl daemon-reload && systemctl restart ollama`

## Ollama modellen

Download de gewenste modellen na de installatie:

```bash
ollama pull qwen2.5:72b     # ~47 GB — primair conversiemodel, beste kwaliteit
ollama pull qwen2.5:32b     # ~20 GB — goede balans kwaliteit/snelheid
ollama pull qwen2.5:7b      # ~4.7 GB — snel, basisgebruik
ollama pull llama3.3:70b    # ~43 GB — alternatief voor qwen2.5:72b
ollama pull qwen2.5vl:7b    # ~5.5 GB — vision model voor afbeeldingsbeschrijving
```

| Ollama model | LiteLLM naam | Grootte | Gebruik |
|---|---|---|---|
| `qwen2.5:72b` | `qwen2.5-72b` | ~47 GB | Beste kwaliteit Nederlandse tekst |
| `qwen2.5:32b` | `qwen2.5-32b` | ~20 GB | Goede balans kwaliteit/snelheid |
| `qwen2.5:7b` | `qwen2.5-7b` | ~4.7 GB | Snelste optie (~5 min/artikel) |
| `llama3.3:70b` | `llama3.3-70b` | ~43 GB | Meta model, vergelijkbaar met qwen2.5:72b |
| `qwen2.5vl:7b` | `qwen2.5vl-7b` | ~5.5 GB | **Vision model** — beschrijft afbeeldingen als gen-prompt |

> **Let op naamgeving:** Ollama gebruikt `qwen2.5vl:7b` (met punt), LiteLLM exposeert dit als `qwen2.5vl-7b` (met koppelteken). De oude naam `qwen2-vl:7b` (zonder punt en versienummer) werkt niet meer.

## Afbeeldingen genereren

De Image Gen Service ondersteunt twee backends:

**Lokaal (diffusers, CPU):**

| Model | `image_model` waarde | Stappen | Resolutie | Opmerking |
|---|---|---|---|---|
| Stable Diffusion XL 1.0 | `sdxl` | 20 | 1024×1024 | Model ~6 GB, eerste keer downloaden van HuggingFace |
| SDXL Turbo | `sdxl-turbo` | 4 | 1024×1024 | Sneller, iets minder kwaliteit |
| Stable Diffusion 1.5 | `sd15` | 20 | max 512×512 | Kleinste model, meest geheugenefficiënt |

Geen API-key nodig. Traag op CPU (geen GPU op deze VM).

**Replicate API (cloud):**
- Sneller, betere kwaliteit
- Vereist Replicate API-key (invoerbaar in Blog Convertor UI)
- Beschikbare modellen: `sdxl`, `flux-schnell`, `flux-dev`

## Beheer

```bash
# LiteLLM
docker logs litellm -f
docker restart litellm

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
docker restart litellm
```

## Gerelateerde repositories

| Repo | Inhoud |
|---|---|
| [n8n-workinglocal](https://github.com/WorkingLocal/n8n-workinglocal) | n8n workflows (incl. Blog Convertor) |
| [vps-workinglocal](https://github.com/WorkingLocal/vps-workinglocal) | Blog Convertor UI (Node.js, VPS poort 3456) |
| [onpremise-workinglocal](https://github.com/WorkingLocal/onpremise-workinglocal) | On-premise Working Local server |
