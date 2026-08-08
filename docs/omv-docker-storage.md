# OMV Docker Storage Integration

## Overview

The homelab uses OpenMediaVault (OMV) as centralized NAS storage for the Ubuntu Docker host.

The OMV `Data` SMB share is mounted on Ubuntu and is available to Docker containers through bind mounts.

## Storage Architecture

```text
OpenMediaVault NAS
        │
        │ SMB 3.0
        ▼
//192.168.1.137/Data
        │
        ▼
/mnt/omv-data
        │
        ├── backups/
        │
        └── docker/
            ├── backups/
            ├── documents/
            ├── immich/
            └── nextcloud/
