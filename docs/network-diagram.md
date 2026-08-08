# Homelab Network & Infrastructure Diagram

## Overview

This document describes the current network and virtualization architecture of the homelab.

The environment uses Proxmox VE as the virtualization platform, with Ubuntu Server hosting Docker-based services and OpenMediaVault providing NAS storage.

---

## Network Architecture

```text
                              Internet
                                  │
                                  ▼
                            Cloudflare
                                  │
                                  │ HTTPS / Tunnel
                                  ▼
                           Home Router
                          192.168.1.1
                                  │
                         192.168.1.0/24
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    Proxmox VE   │
                         │   Virtual Host  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
            ┌───────────────┐           ┌───────────────┐
            │ Ubuntu Server │           │ OpenMediaVault│
            │ Docker Host   │           │    VM 200     │
            └───────┬───────┘           └───────┬───────┘
                    │                            │
                    │ Docker                     │
          ┌─────────┼──────────┐                 │
          │         │          │                 │
          ▼         ▼          ▼                 ▼
      Nextcloud  Vaultwarden Authentik       200 GB
          │         │          │              NAS Disk
          │         │          │                 │
          └─────────┴──────────┘                 │
                    │                            │
                    ▼                            ▼
              Web Services                 SMB/CIFS Share
                                                 │
                                                 ▼
                                           Windows Client
```

---

## Network

### Local Network

| Component       | Address                 |
| --------------- | ----------------------- |
| Network         | `192.168.1.0/24`        |
| Gateway         | `192.168.1.1`           |
| OMV             | `192.168.1.137`         |
| Proxmox         | Host-managed            |
| Docker services | Hosted on Ubuntu Server |

---

## Virtualization

Proxmox VE provides the virtualization layer.

### OpenMediaVault VM

| Setting   | Value            |
| --------- | ---------------- |
| VM ID     | 200              |
| Name      | `openmediavault` |
| CPU       | 2 cores          |
| RAM       | 4 GB             |
| OS disk   | 64 GB            |
| Data disk | 200 GB           |
| Network   | VirtIO           |
| Interface | `ens18`          |
| IP        | `192.168.1.137`  |

---

## Storage Architecture

The OMV VM uses separate virtual disks for the operating system and NAS data.

```text
OMV VM
│
├── /dev/sda
│   └── 64 GB
│       └── Operating System
│
└── /dev/sdb
    └── 200 GB
        └── /dev/sdb1
            └── EXT4
                └── Data/
```

The data filesystem is mounted at:

```text
/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5
```

---

## Docker Services

Ubuntu Server is used as the Docker host for several self-hosted services.

Current services include:

* Nextcloud
* Vaultwarden
* Authentik
* Uptime Kuma
* Nginx Proxy Manager
* Other supporting containers

Docker provides container isolation, persistent volumes, networking, and service management.

---

## External Access

Cloudflare Tunnel is used to provide external HTTPS access to selected services.

The general flow is:

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
Homelab Services
```

This architecture avoids directly exposing inbound ports from the home network.

---

## NAS Access

Windows clients access the OMV NAS through SMB/CIFS.

Example:

```text
\\192.168.1.137\Data
```

The share uses authenticated access rather than anonymous guest access.

---

## Security Considerations

Current security practices include:

* Authenticated SMB access
* Cloudflare Tunnel for external services
* HTTPS for public services
* Secrets excluded from Git
* Dedicated service accounts
* Docker container isolation
* Separate OS and data storage
* Infrastructure documentation

---

## Backup Status

A dedicated physical backup disk is not currently available.

The 200 GB OMV disk should therefore not be considered a complete backup solution.

Planned improvement:

```text
Primary Data
     │
     ▼
OMV NAS
     │
     ▼
Dedicated Backup Storage
     │
     ▼
Off-site / Additional Backup
```

The long-term goal is to implement a **3-2-1 backup strategy**.

---

## Skills Demonstrated

This architecture provides hands-on experience with:

* Proxmox VE
* Virtualization
* Linux administration
* Docker
* Docker Compose
* Networking
* IPv4
* DNS
* HTTPS
* Cloudflare Tunnel
* Reverse proxies
* NAS administration
* EXT4
* SMB/CIFS
* Authentication
* Monitoring
* Git/GitHub
* Infrastructure documentation

---

## Future Improvements

* [ ] Add dedicated physical backup storage
* [ ] Implement 3-2-1 backups
* [ ] Add network segmentation/VLANs
* [ ] Add dedicated monitoring dashboards
* [ ] Add physical NAS storage
* [ ] Document disaster recovery
* [ ] Perform a restore test
* [ ] Add updated infrastructure screenshots
