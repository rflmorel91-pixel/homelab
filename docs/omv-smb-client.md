# OpenMediaVault SMB Client Integration

## Overview

The Ubuntu Server Docker host connects to the OpenMediaVault NAS using SMB/CIFS.

This provides centralized network storage that can be accessed by the Ubuntu host and, later, Docker services.

## Storage Server

| Component | Value |
|---|---|
| Server | OpenMediaVault |
| IP Address | 192.168.1.137 |
| Share | Data |
| Protocol | SMB/CIFS |
| SMB Version | 3.0 |
| Filesystem | EXT4 |
| Capacity | 196 GB |

## Ubuntu Mount

The SMB share is mounted at:

```text
/mnt/omv-data
