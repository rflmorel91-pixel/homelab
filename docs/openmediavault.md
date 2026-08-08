# OpenMediaVault NAS — Homelab Documentation

## Overview

OpenMediaVault (OMV) was deployed as a virtual machine on Proxmox VE to provide NAS storage and SMB/CIFS file sharing to Windows clients.

This project demonstrates practical experience with:

* Proxmox virtualization
* Debian/Linux administration
* OpenMediaVault
* Virtual disk management
* EXT4 filesystems
* Storage mounting
* SMB/CIFS file sharing
* Linux networking
* Windows network shares
* Basic infrastructure troubleshooting

---

## Infrastructure

### Proxmox VM

| Setting           | Value                          |
| ----------------- | ------------------------------ |
| VM ID             | 200                            |
| VM Name           | openmediavault                 |
| OS                | OpenMediaVault 8.3.1           |
| Base OS           | Debian GNU/Linux 13.5 (Trixie) |
| CPU               | 2 cores                        |
| RAM               | 4 GB                           |
| Network           | VirtIO                         |
| Network Interface | ens18                          |
| IP Address        | 192.168.1.137                  |
| Gateway           | 192.168.1.1                    |

### Storage

| Device     |   Size | Purpose              |
| ---------- | -----: | -------------------- |
| `/dev/sda` |  64 GB | OMV operating system |
| `/dev/sdb` | 200 GB | NAS data             |

The operating-system disk and NAS data disk are intentionally separated.

---

## Storage Configuration

The 200 GB virtual disk was added to the OMV VM from the Proxmox host.

Proxmox configuration:

```text
scsi0: local-lvm:vm-200-disk-0,size=64G
scsi1: local-lvm:vm-200-disk-1,size=200G
```

Inside OMV:

```text
/dev/sdb
└── /dev/sdb1
    └── EXT4
```

Filesystem UUID:

```text
b3f81412-c245-4670-9fc1-1d0c80c74fe5
```

Mount point:

```text
/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5
```

Filesystem capacity:

```text
Size: 196G
Used: 2.1M
Available: 196G
Usage: 1%
```

---

## Network Configuration

OMV uses the Proxmox VirtIO network adapter:

```text
Interface: ens18
IP: 192.168.1.137/24
Gateway: 192.168.1.1
```

Network verification:

```bash
ip -br addr
```

Example:

```text
ens18    UP    192.168.1.137/24
```

Routing verification:

```bash
ip route
```

---

## OMV Services

The OpenMediaVault engine was verified as running:

```bash
systemctl is-active openmediavault-engined
```

Result:

```text
active
```

The Nginx web server was also verified:

```bash
systemctl is-active nginx
```

Result:

```text
active
```

---

## Avahi Troubleshooting

During the system health check, the following service reported a failure:

```text
avahi-daemon.service
```

The relevant error was:

```text
Failed to create server: No suitable network protocol available
```

The OMV engine, Nginx, and network connectivity were unaffected.

Because Avahi/mDNS discovery was not required for this NAS deployment, the service was disabled:

```bash
systemctl disable --now avahi-daemon.service avahi-daemon.socket
```

The failed service state was subsequently cleared.

This troubleshooting step demonstrated the ability to identify a non-critical failed service without unnecessarily reinstalling or modifying the operating system.

---

## Shared Folder

A shared folder named `Data` was created on the 200 GB NAS filesystem.

```text
Name: Data
Device: /dev/sdb1
Relative Path: Data/
```

Absolute path:

```text
/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5/Data/
```

---

## SMB/CIFS

SMB/CIFS was configured to provide Windows network access to the `Data` shared folder.

Windows clients can access the share using:

```text
\\192.168.1.137\Data
```

A dedicated OMV user was created for authenticated SMB access rather than using the Linux `root` account.

Guest access was not used.

---

## Verification

### Disk verification

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
```

Result:

```text
sda      64G  disk                    QEMU HARDDISK
├─sda1 60.7G  part ext4   /           
└─sda5  3.3G  part swap   [SWAP]

sdb     200G  disk                    QEMU HARDDISK
└─sdb1       ext4
```

### Filesystem verification

```bash
findmnt /dev/sdb1
```

Result:

```text
/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5
```

### Storage capacity verification

```bash
df -h /srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5
```

Result:

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1       196G  2.1M  196G   1%
```

---

## Troubleshooting Performed

### Problem 1 — OMV ISO missing

The VM initially failed to start because the configured ISO no longer existed in Proxmox storage.

The invalid ISO reference was removed and the VM was configured to boot from the OS disk.

### Problem 2 — VM repeatedly booted into installer

The OMV ISO was removed from the VM after installation.

Boot order was changed to:

```text
scsi0 → net0
```

The VM then successfully booted from the installed OMV system.

### Problem 3 — OMV login

The root account created during installation was used for console administration.

The OMV web interface uses a separate administrative account.

### Problem 4 — Filesystem not initially visible

The 200 GB disk was detected by Linux but was initially not visible as a usable filesystem in the OMV interface.

The disk was verified with:

```bash
lsblk -f
blkid /dev/sdb1
```

OMV configuration was then deployed with:

```bash
omv-salt deploy run fstab
```

The filesystem was successfully mounted.

---

## Current Architecture

```text
                         Home Network
                              │
                              │
                       192.168.1.0/24
                              │
                    ┌─────────┴─────────┐
                    │     Proxmox       │
                    │                   │
                    │     VM 200        │
                    │  OpenMediaVault   │
                    │                   │
                    │  192.168.1.137    │
                    │       │           │
                    │       │ SMB       │
                    │       ▼           │
                    │   200 GB Data     │
                    │     /dev/sdb1     │
                    └─────────┬─────────┘
                              │
                              ▼
                       Windows Client
                    \\192.168.1.137\Data
```

---

## Backup Plan

A dedicated backup disk is **not currently available**.

The current NAS storage should therefore be considered **primary/test storage rather than a backup**.

Future improvements:

* Add a dedicated physical backup HDD/SSD
* Configure scheduled Proxmox VM backups
* Back up important NAS data
* Implement backup retention
* Test restoration
* Work toward a 3-2-1 backup strategy

---

## Skills Demonstrated

This project demonstrates hands-on experience with:

* Linux server administration
* Debian
* Proxmox VE
* Virtual machines
* Virtual disk provisioning
* SCSI storage
* EXT4
* Linux mount points
* Filesystem UUIDs
* systemd
* Network configuration
* DHCP
* SMB/CIFS
* Windows network shares
* OpenMediaVault
* Service troubleshooting
* Infrastructure documentation

---

## Lessons Learned

1. Keep the operating-system disk separate from data storage.
2. Always verify disk names before formatting or wiping.
3. Do not use the Linux `root` account for SMB file sharing.
4. A failed service does not necessarily mean the entire server is broken.
5. Verify networking before troubleshooting application services.
6. Virtual NAS storage is useful for learning, but important data requires independent backups.
7. Documentation is part of infrastructure administration.

---

## Future Improvements

Planned enhancements:

* [ ] Add physical NAS storage
* [ ] Add dedicated backup storage
* [ ] Configure automated Proxmox backups
* [ ] Implement 3-2-1 backup strategy
* [ ] Test NAS restore procedures
* [ ] Add monitoring with Uptime Kuma
* [ ] Add SMART disk monitoring when physical disks are available
* [ ] Document disaster recovery procedures
* [ ] Add screenshots to this project
* [ ] Create network topology diagram

---

## Project Status

**Status: Operational**

OpenMediaVault is running as VM 200 on Proxmox with:

* 64 GB operating-system disk
* 200 GB EXT4 NAS data disk
* 192.168.1.137 network address
* SMB/CIFS Windows file sharing
* Authenticated user access

The NAS is ready for non-critical homelab storage and continued infrastructure development.
