# ai-node-i9 — Minisforum MS-01 i9

## Hardware

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 9 (of i9) |
| RAM | 64 GB |
| Opslag | 4 TB NVMe (OS + modellen) + 2 TB NVMe + 1 TB NVMe |
| iGPU | Intel Arc (geïntegreerd) |
| LAN | 2× 2.5GbE (bonding naar switch) |
| IP (vast) | 192.168.111.31 |
| Tailscale IP | TBD na installatie |
| Hostname | ai-node-i9 |
| OS | Ubuntu 24.04 LTS (bare metal) |

## Rol

Primaire AI compute node. Zwaardere modellen (32B–72B) en hogere throughput dan de ai-engine VM.

## Services (te installeren)

| Service | Poort | Type |
|---|---|---|
| Ollama | 11434 | systemd |
| LiteLLM | 4000 | Docker |

## Netwerk

Beide 2.5GbE poorten verbonden met Unifi USW-Pro-Max 24 PoE via LACP bond (optioneel) of active-backup.
Fixed IP via Unifi DHCP reservation: 192.168.111.31

## Installatiestatus

- [ ] Ubuntu 24.04 installeren
- [ ] Tailscale instellen
- [ ] Ollama installeren + iGPU configureren
- [ ] LiteLLM Docker container
- [ ] Modellen downloaden
- [ ] Integreren in LiteLLM config van ai-engine
- [ ] Fixed IP toewijzen in Unifi
