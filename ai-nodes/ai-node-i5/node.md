# ai-node-i5 — Minisforum MS-01 i5

## Hardware

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 5 (i5) |
| RAM | 32 GB |
| Opslag | TBD |
| iGPU | Intel Arc (geïntegreerd) |
| LAN | 10GbE SFP+ (enp2s0f0np0) — actieve verbinding |
| Netwerk IP (vast) | 192.168.111.32 |
| Tailscale IP | 100.78.175.49 |
| Hostname | ai-node-i5 |
| OS | Ubuntu 24.04 LTS (bare metal) |
| Gebruiker | hostinglocal / hostinglocal |

## Rol

Secundaire AI compute node voor lichtere modellen (7B) en snelle inference.
Vroeger: WORKSTATION / WEBSERVER — nu herbestemd als compute node.

## Services

| Service | Poort | Type | Status |
|---|---|---|---|
| Ollama | 11434 | systemd | ✅ actief |
| node_exporter | 9100 | systemd | ✅ actief |
| LiteLLM | 4000 | Docker | TODO |

## Netwerk

10GbE SFP+ (enp2s0f0np0) — verbonden met Unifi Aggregation Switch.
Static IP via netplan: `/etc/netplan/60-static.yaml` → 192.168.111.32/24, gateway 192.168.111.1.

## Ollama configuratie

Systemd override: `/etc/systemd/system/ollama.service.d/override.conf`

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_NUM_PARALLEL=4"
```

## Beheer

```bash
# SSH via Tailscale
ssh hostinglocal@100.78.175.49

# Ollama
ollama list
ollama ps
systemctl status ollama

# Node exporter
curl http://localhost:9100/metrics | head -5
```

## Installatiestatus

- [x] Ubuntu 24.04 installeren
- [x] Statisch IP instellen (192.168.111.32 via netplan, 10GbE)
- [x] Tailscale instellen (100.78.175.49)
- [x] Ollama installeren (OLLAMA_HOST=0.0.0.0, NUM_PARALLEL=4)
- [x] Intel Arc iGPU drivers installeren (intel-opencl-icd, level-zero)
- [x] node_exporter installeren (v1.8.2, poort 9100)
- [x] Prometheus scrape target toegevoegd
- [x] Coolify SSH key toegevoegd (beheerbaar via Coolify UI)
- [ ] Coolify server toevoegen via UI (SSH: hostinglocal@100.78.175.49)
- [ ] qwen2.5:7b model downloaden
- [ ] LiteLLM Docker container + integreren in ai-engine config
- [ ] Fixed IP toewijzen in Unifi DHCP reservation
