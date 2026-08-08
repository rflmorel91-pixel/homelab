# Docker Infrastructure Documentation

## Overview

The homelab uses Docker on an Ubuntu Server host to run and manage self-hosted applications.

Docker provides container isolation, application deployment, networking, persistent storage, and service management.

---

## Docker Host

| Component        | Value              |
| ---------------- | ------------------ |
| Hostname         | `dellpc`           |
| Operating System | Ubuntu Linux       |
| Kernel           | `7.0.0-29-generic` |
| Architecture     | `x86_64`           |
| Docker Engine    | `29.1.3`           |
| Docker Compose   | `v2.29.2`          |
| Compose command  | `docker-compose`   |

---

## Container Architecture

```text
                         Ubuntu Server
                              │
                              ▼
                            Docker
                              │
       ┌──────────────┬───────┼────────┬──────────────┐
       │              │       │        │              │
       ▼              ▼       ▼        ▼              ▼
   Nextcloud      Authentik  Immich  Vaultwarden   Portainer
       │              │       │
       │              │       ├── PostgreSQL
       │              │       ├── Redis
       │              │       └── Machine Learning
       │              │
       ├── MariaDB    ├── PostgreSQL
       └── Redis      └── Redis

       Additional services:
       ├── Nginx Proxy Manager
       ├── Cloudflared
       ├── Uptime Kuma
       └── Stirling PDF
```

---

## Running Containers

The following containers are currently running.

| Container                 | Image                                 | Purpose                     |
| ------------------------- | ------------------------------------- | --------------------------- |
| `uptime-kuma`             | `louislam/uptime-kuma:latest`         | Service monitoring          |
| `stirling-pdf`            | `stirlingtools/stirling-pdf:latest`   | PDF processing              |
| `cloudflared`             | `cloudflare/cloudflared:latest`       | Cloudflare Tunnel           |
| `immich_server`           | `ghcr.io/immich-app/immich-server:v3` | Photo management            |
| `immich_postgres`         | Immich PostgreSQL image               | Immich database             |
| `immich_machine_learning` | Immich ML image                       | Machine learning            |
| `immich_redis`            | `valkey/valkey:9`                     | Immich cache                |
| `authentik-worker`        | `ghcr.io/goauthentik/server:latest`   | Authentik background worker |
| `authentik`               | `ghcr.io/goauthentik/server:latest`   | Identity provider           |
| `authentik-postgres`      | `postgres:16`                         | Authentik database          |
| `authentik-redis`         | `redis:7`                             | Authentik cache             |
| `vaultwarden`             | `vaultwarden/server:latest`           | Password management         |
| `nginx-proxy-manager`     | `jc21/nginx-proxy-manager:latest`     | Reverse proxy               |
| `nextcloud`               | `nextcloud:latest`                    | Cloud file platform         |
| `nextcloud-redis`         | `redis:7-alpine`                      | Nextcloud cache             |
| `nextcloud-db`            | `mariadb:11`                          | Nextcloud database          |
| `portainer`               | `portainer/portainer-ce:latest`       | Docker management           |

**Total running containers: 17**

---

## Docker Compose Projects

The environment contains several Docker Compose projects.

| Project               | Containers |
| --------------------- | ---------: |
| `nextcloud`           |          3 |
| `authentik`           |          4 |
| `immich`              |          4 |
| `nginx-proxy-manager` |          1 |
| `uptime-kuma`         |          1 |
| `stirling-pdf`        |          1 |
| `vaultwarden`         |          1 |

Some services, including Portainer and Cloudflared, are not currently reporting a Docker Compose project label.

---

## Docker Networks

The Docker host currently contains the following networks:

| Network                       | Driver | Purpose                         |
| ----------------------------- | ------ | ------------------------------- |
| `authentik_default`           | bridge | Authentik services              |
| `bridge`                      | bridge | Default Docker network          |
| `host`                        | host   | Host networking                 |
| `immich_default`              | bridge | Immich services                 |
| `nextcloud_default`           | bridge | Nextcloud services              |
| `nginx-proxy-manager_default` | bridge | Nginx Proxy Manager             |
| `none`                        | null   | Disabled networking             |
| `npm`                         | bridge | Shared/reverse-proxy networking |
| `stirling-pdf_default`        | bridge | Stirling PDF                    |

### Network Design

Docker Compose creates separate bridge networks for several application stacks.

This provides logical separation between services while allowing containers within the same application stack to communicate directly.

The `npm` network is also available for connecting services to Nginx Proxy Manager when reverse-proxy access is required.

---

## Persistent Storage

Docker uses named volumes to persist application data outside the container filesystem.

### Application Volumes

| Volume                                | Application                      |
| ------------------------------------- | -------------------------------- |
| `authentik_postgres_data`             | Authentik PostgreSQL             |
| `authentik_redis_data`                | Authentik Redis                  |
| `immich_model-cache`                  | Immich ML                        |
| `nextcloud_db_data`                   | Nextcloud database               |
| `nextcloud_nextcloud_data`            | Nextcloud application data       |
| `nginx-proxy-manager_npm_data`        | Nginx Proxy Manager              |
| `nginx-proxy-manager_npm_letsencrypt` | Nginx Proxy Manager certificates |
| `portainer-data`                      | Portainer                        |
| `portainer_data`                      | Portainer                        |
| `stirling-pdf_stirling_configs`       | Stirling PDF configuration       |
| `stirling-pdf_stirling_logs`          | Stirling PDF logs                |
| `stirling-pdf_stirling_pipeline`      | Stirling PDF pipeline            |
| `stirling-pdf_stirling_tessdata`      | Stirling PDF OCR data            |
| `uptime-kuma_uptime-kuma`             | Uptime Kuma                      |
| `vaultwarden_vaultwarden_data`        | Vaultwarden                      |

Additional Docker volumes with generated identifiers are also present.

---

## Published Services

Several containers publish ports from Docker to the host.

| Service                   | Port   |
| ------------------------- | ------ |
| Uptime Kuma               | `3001` |
| Stirling PDF              | `8082` |
| Immich                    | `2283` |
| Authentik                 | `9000` |
| Nginx Proxy Manager HTTP  | `80`   |
| Nginx Proxy Manager Admin | `81`   |
| Nginx Proxy Manager HTTPS | `443`  |
| Nextcloud                 | `8080` |
| Portainer HTTP            | `8000` |
| Portainer HTTPS           | `9443` |

Other containers expose their ports only internally to their Docker networks.

---

## Reverse Proxy

Nginx Proxy Manager provides reverse-proxy functionality for selected services.

General architecture:

```text
                    Internet
                       │
                       ▼
                  Cloudflare
                       │
                       ▼
                Cloudflare Tunnel
                       │
                       ▼
              Nginx Proxy Manager
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
      Nextcloud    Vaultwarden   Authentik
```

This allows services to be accessed through hostnames without requiring every application to expose its own public-facing port.

---

## Cloudflare Tunnel

The `cloudflared` container provides the Cloudflare Tunnel connection.

Purpose:

* External HTTPS access
* DNS-based hostname routing
* Reduced need for inbound router port forwarding
* Secure access to selected homelab applications

---

## Management

Portainer provides a graphical interface for Docker administration.

Management tasks include:

* Container status
* Container logs
* Images
* Volumes
* Networks
* Container restart operations
* Resource monitoring

The command line remains available for troubleshooting and administration.

---

## Monitoring

Uptime Kuma provides service availability monitoring.

Current monitoring can be used to track:

* Web services
* HTTP endpoints
* Application availability
* Service outages

This provides an additional operational layer beyond simply checking whether a Docker container is running.

---

## Security Practices

The Docker environment follows several security practices:

* Secrets are excluded from Git repositories.
* Sensitive environment files are not committed.
* Persistent data is stored in Docker volumes.
* Services are separated into application-specific networks.
* External access is routed through Cloudflare where appropriate.
* Nginx Proxy Manager handles reverse-proxy requirements.
* Containers are monitored for health and availability.
* Administrative interfaces are not intended to be publicly exposed.

---

## Troubleshooting Workflow

When a containerized service fails, the following workflow is used.

### Check running containers

```bash
docker ps
```

### Check all containers

```bash
docker ps -a
```

### Check container logs

```bash
docker logs <container-name>
```

### Follow logs

```bash
docker logs -f <container-name>
```

### Inspect a container

```bash
docker inspect <container-name>
```

### Check networks

```bash
docker network ls
```

### Inspect a network

```bash
docker network inspect <network-name>
```

### Check volumes

```bash
docker volume ls
```

---

## Docker Compose

The host currently uses the standalone Docker Compose command:

```bash
docker-compose
```

Version:

```text
Docker Compose v2.29.2
```

The newer plugin syntax:

```bash
docker compose
```

is not currently available on this host.

Compose projects are used to define multi-container applications such as:

* Nextcloud
* Authentik
* Immich
* Nginx Proxy Manager
* Uptime Kuma
* Stirling PDF
* Vaultwarden

---

## Backup Considerations

Docker volumes contain important application data.

Critical data includes:

* Nextcloud files
* Nextcloud database
* Vaultwarden database/data
* Authentik database
* Immich database and media
* Nginx Proxy Manager configuration
* Let's Encrypt certificates
* Uptime Kuma configuration

A future backup strategy should include both:

1. Application configuration
2. Persistent application data

The long-term goal is to integrate Docker backups with the homelab's NAS and a 3-2-1 backup strategy.

---

## Skills Demonstrated

This Docker environment provides hands-on experience with:

* Docker Engine
* Docker Compose
* Container management
* Container networking
* Persistent volumes
* Reverse proxies
* Application deployment
* Service monitoring
* Container troubleshooting
* Database containers
* Redis/Valkey
* PostgreSQL
* MariaDB
* Cloudflare Tunnel
* Infrastructure documentation
* Git/GitHub

---

## Future Improvements

* [ ] Standardize Docker Compose usage
* [ ] Document every Compose project
* [ ] Add Docker resource monitoring
* [ ] Implement automated volume backups
* [ ] Back up Docker Compose files
* [ ] Document restore procedures
* [ ] Add container update strategy
* [ ] Implement centralized logging
* [ ] Improve network segmentation
* [ ] Integrate Docker backups with OpenMediaVault
* [ ] Test disaster recovery procedures

---

## Project Status

**Status: Operational**

The Docker environment is actively used as the application platform for the homelab.

The infrastructure continues to evolve as new services, monitoring, security controls, and backup capabilities are added.
