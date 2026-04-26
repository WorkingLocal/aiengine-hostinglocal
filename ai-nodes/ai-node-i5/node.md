# ai-node-i5 — Minisforum MS-01 i5

## Hardware

| Parameter | Waarde |
|---|---|
| Model | Minisforum MS-01 |
| CPU | Intel Core Ultra 5 (i5) |
| RAM | 32 GB |
| Opslag | TBD (was WORKSTATION, geherinstalleerd) |
| iGPU | Intel Arc (geïntegreerd) |
| LAN | 2× 2.5GbE |
| IP (vast) | 192.168.111.32 |
| Tailscale IP | TBD na installatie |
| Hostname | ai-node-i5 |
| OS | Ubuntu 24.04 LTS (bare metal, al geherinstalleerd) |

## Rol

Secundaire AI compute node voor lichtere modellen (7B) en snelle inference.
Vroeger: WORKSTATION / WEBSERVER — nu herbestemd als compute node.

## Services (te installeren)

| Service | Poort | Type |
|---|---|---|
| Ollama | 11434 | systemd |
| LiteLLM | 4000 | Docker (optioneel, of via centrale LiteLLM) |

## Installatiestatus

- [ ] Tailscale instellen
- [ ] Ollama installeren + iGPU configureren
- [ ] Modellen downloaden
- [ ] Integreren in LiteLLM config van ai-engine
- [ ] Fixed IP toewijzen in Unifi (192.168.111.32)
