# Homelab Monitoring & Reliability

## Overview

The homelab uses Uptime Kuma for basic HTTP availability monitoring.

Monitoring is performed every 60 seconds against selected public HTTPS services.

## Monitored Services

| Service | Endpoint | Monitoring |
|---|---|---|
| Nextcloud | https://cloud.fieldlookers.com | HTTP |
| Vaultwarden | https://vault.fieldlookers.com | HTTP |
| Authentik | https://auth.fieldlookers.com | HTTP |
| Cloudflare Tunnel | Public endpoint check | HTTP |

## Current Monitoring Results

### Nextcloud

- Current status: Up
- Check interval: 60 seconds
- Current response: 418 ms
- 24-hour average: 391 ms
- 24-hour uptime: 89.98%
- 30-day uptime: 95.11%
- Certificate expiration: 2026-11-02

### Vaultwarden

- Current status: Up
- Check interval: 60 seconds
- Current response: 157 ms
- 24-hour average: 173 ms
- 24-hour uptime: 100%
- 30-day uptime: 100%
- Certificate expiration: 2026-11-02

### Authentik

- Current status: Up
- Check interval: 60 seconds
- Current response: 619 ms
- 24-hour average: 583 ms
- 24-hour uptime: 35.08%
- 30-day uptime: 68.13%
- Certificate expiration: 2026-11-02

### Cloudflare Tunnel

- Current status: Up
- Check interval: 60 seconds
- Current response: 364 ms
- 24-hour average: 399 ms
- 24-hour uptime: 90.05%
- 30-day uptime: 95.13%
- Certificate expiration: 2026-11-02

## Incident History

Uptime Kuma recorded HTTP 502 responses affecting Nextcloud, Authentik, and the Cloudflare Tunnel monitor.

These incidents were investigated by checking:

- Docker container status
- Docker restart policies
- Docker network membership
- Container DNS resolution
- Nginx Proxy Manager connectivity
- Authentik connectivity
- Cloudflare Tunnel status
- Public HTTPS endpoints

## Recovery Verification

The homelab was also tested following a power outage.

Verified:

- Docker starts automatically at boot
- Cloudflare Tunnel starts automatically
- Core containers use `unless-stopped`
- Nginx Proxy Manager recovers
- Nextcloud recovers
- Vaultwarden recovers
- Authentik recovers
- Uptime Kuma recovers

## Lessons Learned

The monitoring data demonstrates that service availability depends on more than whether a Docker container is running.

Troubleshooting required checking the complete request path:

```text
Internet
   ↓
Cloudflare
   ↓
Cloudflare Tunnel
   ↓
Nginx Proxy Manager
   ↓
Docker Network
   ↓
Application Container
   ↓
Application
```

## Future Improvements

Planned monitoring improvements include:

- Monitor Nginx Proxy Manager directly
- Add an independent Cloudflare Tunnel health check
- Add internal service checks
- Monitor Docker container health
- Monitor CPU and memory usage
- Monitor disk usage
- Monitor NAS storage
- Configure notifications
- Track recovery time after outages
- Document recurring incidents
