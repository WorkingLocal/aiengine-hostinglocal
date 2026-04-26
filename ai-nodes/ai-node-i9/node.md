# ai-node-i9 — Minisforum MS-01 i9

## Hardware

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 9 (i9-13900H) |
| RAM | 64 GB (62 GiB gerapporteerd) |
| Opslag | 4 TB NVMe (OS + modellen) + 2 TB NVMe + 1 TB NVMe |
| iGPU | Intel Arc (geïntegreerd) |
| LAN | 10GbE SFP+ (enp2s0f0np0) — actieve verbinding |
| Netwerk IP (vast) | 192.168.111.31 |
| Tailscale IP | 100.126.121.11 |
| Hostname | ai-node-i9 |
| OS | Ubuntu 24.04 LTS (bare metal) |
| Gebruiker | hostinglocal / hostinglocal |

## Rol

Primaire AI compute node. Zwaardere modellen (32B–72B) en hogere throughput dan de ai-engine VM.

## Services

| Service | Poort | Type | Status |
|---|---|---|---|
| Ollama | 11434 | systemd | ✅ actief |
| node_exporter | 9100 | systemd | ✅ actief |
| LiteLLM | 4000 | Docker | TODO |

## Netwerk

10GbE SFP+ (enp2s0f0np0, MAC 58:47:ca:78:bd:7a) — verbonden met Unifi Aggregation Switch.
Enkel 10GbE verbinding in gebruik (2.5GbE verwijderd voor eenvoud).
Static IP via netplan: `/etc/netplan/60-static.yaml` → 192.168.111.31/24, gateway 192.168.111.1.

## Ollama configuratie

Systemd override: `/etc/systemd/system/ollama.service.d/override.conf`

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_NUM_PARALLEL=4"
```

## Geïnstalleerde modellen

| Model | Grootte | Status |
|---|---|---|
| qwen2.5:7b | ~4.7 GB | ✅ geïnstalleerd |

Nog te downloaden (met 64 GB RAM):
- `ollama pull qwen2.5:32b` (~20 GB)
- `ollama pull qwen2.5:72b` (~47 GB)

## Beheer

```bash
# SSH via Tailscale
ssh hostinglocal@100.126.121.11

# Ollama
ollama list
ollama ps
systemctl status ollama

# Node exporter (Prometheus metrics)
curl http://localhost:9100/metrics | head -5
```

## Installatiestatus

- [x] Ubuntu 24.04 installeren (LVM op 4TB NVMe)
- [x] Statisch IP instellen (192.168.111.31 via netplan, 10GbE)
- [x] Tailscale instellen (100.126.121.11)
- [x] Ollama installeren (v0.21.2, OLLAMA_HOST=0.0.0.0, NUM_PARALLEL=4)
- [x] Intel Arc iGPU drivers installeren (intel-opencl-icd, level-zero)
- [x] node_exporter installeren (v1.8.2, poort 9100)
- [x] Prometheus scrape target toegevoegd (metrics-workinglocal/prometheus.yml)
- [x] Coolify SSH key toegevoegd (beheerbaar via Coolify UI)
- [x] qwen2.5:7b model gedownload
- [ ] Coolify server toevoegen via UI (SSH: hostinglocal@100.126.121.11)
- [ ] qwen2.5:32b + qwen2.5:72b modellen downloaden
- [ ] LiteLLM Docker container + integreren in ai-engine config
- [ ] Fixed IP toewijzen in Unifi DHCP reservation
