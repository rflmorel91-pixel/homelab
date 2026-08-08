# Homelab Networking & Reverse Proxy

## Overview

The homelab uses a layered network architecture to provide secure external access to self-hosted applications.

Public requests are routed through Cloudflare Tunnel and Nginx Proxy Manager before reaching Docker containers on isolated Docker networks.

This architecture provides hands-on experience with DNS, HTTPS, reverse proxies, Docker networking, service discovery, and troubleshooting.

---

## Network Architecture

```text
                         Internet
                            │
                            ▼
                       Cloudflare
                            │
                            ▼
                   Cloudflare Tunnel
                     (cloudflared)
                            │
                            ▼
                 Nginx Proxy Manager
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
         Nextcloud      Vaultwarden     Authentik
             │              │              │
             ▼              ▼              ▼
       Docker Network   Docker Network  Docker Network
