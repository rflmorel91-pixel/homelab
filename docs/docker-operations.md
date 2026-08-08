# Docker Operations & Container Management

## Overview

Docker is the primary application platform used by this homelab.

The environment hosts multiple self-hosted applications across several Docker Compose projects. This provides hands-on experience with container deployment, persistent storage, networking, service discovery, health checks, troubleshooting, and recovery.

## Docker Environment

### Docker

* Docker version: 29.1.3
* Operating system: Ubuntu Server
* Docker service: enabled at boot
* Container restart policy: `unless-stopped` for core services

### Docker Compose

Docker Compose is installed as the standalone `docker-compose` command.

* Docker Compose version: v2.29.2

The environment currently uses multiple Compose projects rather than a single monolithic stack.

## Docker Compose Projects

| Project             | Status                 | Compose File                                            |
| ------------------- | ---------------------- | ------------------------------------------------------- |
| Authentik           | Running (4 containers) | `/home/rflmorel/authentik/docker-compose.yml`           |
| Immich              | Running (4 containers) | `/home/rflmorel/immich/docker-compose.yml`              |
| Nextcloud           | Running (3 containers) | `/opt/stacks/nextcloud/docker-compose.yml`              |
| Nginx Proxy Manager | Running (1 container)  | `/home/rflmorel/nginx-proxy-manager/docker-compose.yml` |
| Stirling PDF        | Running (1 container)  | `/data/compose/12/docker-compose.yml`                   |
| Uptime Kuma         | Running (1 container)  | `/data/compose/13/docker-compose.yml`                   |
| Vaultwarden         | Running (1 container)  | `/data/compose/10/docker-compose.yml`                   |

## Running Containers

The environment currently contains 17 running containers.

Major services include:

* Nginx Proxy Manager
* Nextcloud
* Uptime Kuma
* Stirling PDF
* Cloudflare Tunnel
* Immich
* Authentik
* Vaultwarden
* Portainer
* MariaDB
* PostgreSQL
* Redis
* Valkey
* Immich machine learning services

## Container Health

Several services provide Docker health checks.

Verified healthy services include:

* Uptime Kuma
* Stirling PDF
* Immich Server
* Immich PostgreSQL
* Immich machine learning
* Immich Redis
* Authentik
* Authentik Worker
* Vaultwarden

Health checks provide an additional layer of verification beyond simply checking whether a container is running.

## Docker Networking

The environment uses multiple Docker bridge networks.

Current networks include:

* `authentik_default`
* `immich_default`
* `nextcloud_default`
* `nginx-proxy-manager_default`
* `npm`
* `stirling-pdf_default`
* Docker `bridge`
* Docker `host`
* Docker `none`

Multiple application stacks use separate Docker networks.

When services need to communicate across Compose projects, containers can be connected to an additional Docker network.

### Example

Nginx Proxy Manager was connected to the Authentik network:

```bash
docker network connect authentik_default nginx-proxy-manager
```

Container DNS resolution was then verified:

```bash
docker exec nginx-proxy-manager getent hosts authentik
```

Result:

```text
172.21.0.5 authentik
```

Connectivity was verified directly from the Nginx Proxy Manager container:

```bash
docker exec nginx-proxy-manager curl -I http://authentik:9000
```

Authentik returned:

```text
HTTP/1.1 302 Found
```

This confirmed that the reverse proxy container could resolve and communicate with Authentik over the Docker network.

## Persistent Storage

Docker volumes are used to preserve application data independently of container lifecycles.

Important persistent volumes include:

* `nextcloud_nextcloud_data`
* `nextcloud_db_data`
* `vaultwarden_vaultwarden_data`
* `uptime-kuma_uptime-kuma`
* `authentik_postgres_data`
* `authentik_redis_data`
* `portainer_data`
* `portainer-data`
* `nginx-proxy-manager_npm_data`
* `nginx-proxy-manager_npm_letsencrypt`
* `immich_model-cache`
* Stirling PDF configuration and application volumes

Persistent storage allows containers to be recreated or restarted without losing application data.

## Reverse Proxy Architecture

Public applications follow a layered request path:

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

This architecture was used for services including:

* Nextcloud
* Vaultwarden
* Authentik

## Troubleshooting Experience

The homelab has been used to troubleshoot real Docker networking and service availability problems.

Troubleshooting methods included:

### Check container status

```bash
docker ps
```

### Inspect container networks

```bash
docker inspect <container>
```

### Inspect Docker networks

```bash
docker network inspect <network>
```

### Test container DNS resolution

```bash
docker exec <container> getent hosts <service>
```

### Test application connectivity

```bash
docker exec <container> curl -I http://<service>:<port>
```

### Review container logs

```bash
docker logs <container>
```

### Check recent errors

```bash
docker logs --since 24h <container>
```

### Check restart policy

```bash
docker inspect <container> \
  --format '{{.HostConfig.RestartPolicy.Name}}'
```

## Power Outage Recovery

The Docker environment was tested following a power outage.

Recovery verification confirmed:

* Docker starts automatically at boot
* Core containers use `unless-stopped`
* Nginx Proxy Manager recovers
* Nextcloud recovers
* Vaultwarden recovers
* Authentik recovers
* Uptime Kuma recovers
* Cloudflare Tunnel starts automatically

This demonstrates practical experience with service persistence and automatic recovery.

## Operational Skills Demonstrated

This Docker environment demonstrates hands-on experience with:

* Docker installation
* Docker Compose
* Container lifecycle management
* Multi-container applications
* Persistent volumes
* Docker bridge networks
* Cross-network container communication
* Container DNS/service discovery
* Health checks
* Restart policies
* Container logs
* Application troubleshooting
* Reverse proxy integration
* Cloudflare Tunnel integration
* Service recovery
* Infrastructure documentation

## Useful Commands

### List containers

```bash
docker ps
```

### List all containers

```bash
docker ps -a
```

### List Compose projects

```bash
docker-compose ls
```

### List networks

```bash
docker network ls
```

### List volumes

```bash
docker volume ls
```

### Inspect a container

```bash
docker inspect <container>
```

### View logs

```bash
docker logs <container>
```

### Follow logs

```bash
docker logs -f <container>
```

### Restart a container

```bash
docker restart <container>
```

## Summary

This homelab provides hands-on experience managing a multi-service Docker environment with multiple Compose projects, persistent storage, isolated networks, reverse proxy infrastructure, monitoring, authentication, and automated recovery.

The environment is continuously used as a practical learning platform for Linux administration, Docker operations, networking, troubleshooting, security, and infrastructure documentation.
