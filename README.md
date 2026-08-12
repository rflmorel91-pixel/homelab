# Homelab Infrastructure Portfolio

Welcome to my personal IT homelab.

This repository documents my hands-on experience building, administering, monitoring, and documenting a small self-hosted infrastructure environment.

The goal of this project is to continuously develop practical skills in **Linux administration, virtualization, networking, Docker, storage, security, monitoring, and infrastructure documentation**.

---

## 🏗️ Infrastructure Overview

```text
                         Home Network
                              │
                              ▼
                         Proxmox VE
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
          OMV NAS          Ubuntu Server     Other VMs
              │               │
              │               ├── Docker
              │               │     ├── Nextcloud
              │               │     ├── Vaultwarden
              │               │     ├── Authentik
              │               │     ├── Uptime Kuma
              │               │     └── Other Services
              │               │
              ▼               ▼
          SMB Storage      Web Services
              │
              ▼
        Windows Clients
```
## 🖥️ Hardware Platform

The homelab is built on a **Dell OptiPlex 5060** serving as the primary virtualization host.

### Physical Host

* **System:** Dell OptiPlex 5060
* **CPU:** Intel Core i5-8500 @ 3.00 GHz
* **CPU Cores:** 6
* **Memory:** 16 GB DDR4
* **Memory Speed:** 2666 MT/s
* **Storage:** ~1 TB physical disk
* **Hypervisor:** Proxmox VE 9.2.5
* **Host OS:** Debian GNU/Linux 13 (Trixie)
* **Virtualization:** KVM/QEMU
* **Storage Backend:** LVM-thin

### Virtualized Workloads

The physical host provides the virtualization layer for multiple infrastructure workloads, including:

* Ubuntu Server virtual machine
* OpenMediaVault virtual machine
* Docker-based application services
* Storage services
* Monitoring and infrastructure services

The platform provides a compact and power-efficient environment for hands-on experience with virtualization, Linux administration, networking, storage, security, monitoring, and infrastructure automation.

---

## 🌐 Networking & Architecture

The homelab uses a private IPv4 network with Proxmox providing the virtualization layer for the infrastructure.

### Network Configuration

* **Private network:** `192.168.1.0/24`
* **Default gateway:** `192.168.1.1`
* **OpenMediaVault:** `192.168.1.137`
* **OpenMediaVault interface:** `ens18`
* **Ubuntu Server:** Hosts the primary Docker environment
* **Virtualization:** Proxmox VE

### External Access Architecture

```text
                         Internet
                            │
                            ▼
                       Cloudflare
                            │
                     Cloudflare Tunnel
                            │
                            ▼
                    Ubuntu Server VM
                            │
                         Docker
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Nginx Proxy      Nextcloud      Vaultwarden
        Manager                         Authentik
```

Cloudflare Tunnel provides secure external connectivity to selected services without requiring traditional inbound port forwarding on the home network.

Nginx Proxy Manager is used for reverse proxy and HTTPS ingress where applicable, while Docker provides the application hosting environment.

### Internal Services

The internal network supports:

* Proxmox virtualization
* Ubuntu Server workloads
* OpenMediaVault storage
* Docker containers
* SMB file sharing
* Infrastructure monitoring
* Authentication services

Network configuration and service connectivity are documented and verified as part of the ongoing homelab administration process.


## 🚀 Projects

### OpenMediaVault NAS

**Status: Operational**

Built an OpenMediaVault NAS as a virtual machine on Proxmox.

Key components:

* OpenMediaVault 8.3.1
* Debian GNU/Linux 13.5
* 2 CPU cores
* 4 GB RAM
* 64 GB OS disk
* 200 GB dedicated NAS data disk
* EXT4 filesystem
* SMB/CIFS file sharing
* Authenticated Windows access
* Linux storage and filesystem administration

Documentation:

➡️ [OpenMediaVault NAS Documentation](docs/openmediavault.md)

---

### Proxmox Virtualization

**Status: Operational**

Proxmox VE is the virtualization platform for the homelab.

Skills practiced:

* Virtual machine creation
* VM resource allocation
* Virtual disk management
* SCSI storage
* VirtIO networking
* ISO management
* VM boot configuration
* Linux VM administration
* Troubleshooting VM startup problems

---

### Docker Infrastructure

**Status: Operational**

Docker is used to host and manage self-hosted applications.

Skills practiced:

* Docker installation
* Docker Compose
* Container management
* Persistent volumes
* Container networking
* Environment variables
* Service troubleshooting
* Portainer administration

Documentation:

➡️ [Docker Documentation](docker/)

---

### Nextcloud

**Status: Operational**

Self-hosted cloud storage running in Docker.

Skills practiced:

* Docker deployment
* Persistent storage
* Nextcloud administration
* File scanning
* Background jobs
* Trusted domains
* Web access
* Reverse proxy configuration

---

### Vaultwarden

**Status: Operational**

Self-hosted password management using Vaultwarden.

Skills practiced:

* Docker deployment
* Secure configuration
* Environment variables
* Authentication
* Persistent application storage
* Reverse proxy integration

---

### Authentik / SSO

**Status: In Progress**

Authentication infrastructure using Authentik and OpenID Connect.

Current work includes:

* Authentik deployment
* PostgreSQL
* Redis
* OAuth2/OpenID Connect
* Nextcloud OIDC integration
* Application/provider configuration
* Discovery endpoint testing
* Authentication troubleshooting

---

### Cloudflare Tunnel

**Status: Operational**

Cloudflare Tunnel is used to provide secure external access to selected homelab services without directly exposing inbound ports.

Skills practiced:

* Cloudflare Tunnel
* `cloudflared`
* DNS configuration
* Hostname routing
* HTTPS
* Tunnel troubleshooting
* Reverse proxy architecture

---

### Uptime Kuma

**Status: Operational**

Self-hosted monitoring for homelab services.

Example monitored services include:

* Nextcloud
* Vaultwarden
* Web applications
* Network services

Skills practiced:

* Service monitoring
* Availability monitoring
* HTTP monitoring
* Docker deployment
* Troubleshooting outages

---

## 🛠️ Technology Stack

### Virtualization

* Proxmox VE
* QEMU/KVM
* Virtual Machines

### Operating Systems

* Debian
* Ubuntu Server
* Linux command line

### Containers

* Docker
* Docker Compose
* Portainer

### Storage

* OpenMediaVault
* EXT4
* Linux filesystems
* SMB/CIFS
* Virtual disks
* NAS architecture

### Networking

* TCP/IP
* IPv4
* DHCP
* DNS
* HTTP/HTTPS
* Reverse proxies
* Cloudflare Tunnel
* VirtIO networking

### Security & Authentication

* Authentik
* OpenID Connect
* OAuth2
* Vaultwarden
* HTTPS
* Secrets management
* Environment variables

### Monitoring

* Uptime Kuma

### Documentation & Version Control

* Git
* GitHub
* Markdown
* Infrastructure documentation

---

## 📂 Repository Structure

```text
homelab/
│
├── docker/
│   └── Docker-related configuration
│
├── docs/
│   ├── openmediavault.md
│   └── infrastructure documentation
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔐 Security Practices

This repository intentionally does **not** contain:

* Passwords
* API tokens
* Authentication secrets
* Private keys
* Cloudflare credentials
* Database credentials
* `.env` files containing secrets
* Personal sensitive data

Sensitive configuration is stored outside the Git repository.

The `.gitignore` file is used to help prevent accidental commits of secrets and private data.

---

## 📚 Skills I'm Developing

This homelab is being used as a hands-on learning environment to develop skills for IT infrastructure and remote technical roles.

Current areas of focus:

* Linux system administration
* Help desk / technical troubleshooting
* Server administration
* Virtualization
* Docker
* Networking
* Storage
* NAS administration
* Authentication
* Monitoring
* Cloud services
* Infrastructure documentation
* Git and GitHub

---

## 🎯 Current Learning Goals

* [x] Build a Proxmox virtualization environment
* [x] Deploy Ubuntu Server
* [x] Install Docker
* [x] Deploy Portainer
* [x] Deploy Nextcloud
* [x] Deploy Vaultwarden
* [x] Deploy Authentik
* [x] Configure OIDC authentication
* [x] Configure Cloudflare Tunnel
* [x] Deploy Uptime Kuma
* [x] Build OpenMediaVault NAS
* [x] Configure SMB storage
* [x] Document infrastructure in GitHub
* [ ] Add dedicated backup storage
* [ ] Implement a 3-2-1 backup strategy
* [ ] Perform a documented disaster recovery test
* [ ] Improve network segmentation
* [ ] Expand monitoring
* [ ] Continue building portfolio projects

---

## 📈 Homelab Philosophy

The goal of this project is not simply to run applications.

Each service is an opportunity to practice real infrastructure skills:

**Deploy → Configure → Troubleshoot → Monitor → Document → Improve**

Problems encountered during the build are documented because troubleshooting is an important part of real-world IT administration.

---

## 📌 Project Status

This homelab is an active learning and portfolio project.

Infrastructure, documentation, and services will continue to evolve as new technologies and projects are added.

---

## 👨‍💻 About This Project

This homelab represents hands-on practice with modern IT infrastructure technologies and is intended to demonstrate practical skills through real deployments rather than only theoretical coursework.

**Repository:** [github.com/rflmorel91-pixel/homelab](https://github.com/rflmorel91-pixel/homelab)
## 🔄 Reliability & Recovery

### Power Outage Recovery

**Status: Verified**

Tested the homelab's ability to recover after a power outage and confirmed that core infrastructure services restart automatically.

Recovery configuration verified:

* Docker service enabled at boot
* Cloudflare Tunnel service enabled at boot
* Docker containers configured with `unless-stopped` restart policies
* Nextcloud automatically restarts
* Vaultwarden automatically restarts
* Authentik automatically restarts
* Nginx Proxy Manager automatically restarts
* Uptime Kuma automatically restarts
* Public HTTPS services become available after recovery

This test demonstrated practical experience with service persistence, automatic recovery, and post-outage troubleshooting.

### Public Service Verification

The following services were verified through their public HTTPS endpoints:

| Service     | Public Endpoint          | Result                 |
| ----------- | ------------------------ | ---------------------- |
| Nextcloud   | `cloud.fieldlookers.com` | HTTP 302 — Operational |
| Vaultwarden | `vault.fieldlookers.com` | HTTP 200 — Operational |
| Authentik   | `auth.fieldlookers.com`  | HTTP 302 — Operational |

HTTPS ingress is handled through Nginx Proxy Manager, with Cloudflare Tunnel providing external connectivity.

### Monitoring

Uptime Kuma provides basic HTTP availability monitoring for:

* Nextcloud
* Vaultwarden
* Authentik
* Cloudflare Tunnel

Monitoring interval:

* 60 seconds

The monitoring history has also captured temporary HTTP 502 events, providing real-world troubleshooting data rather than simulated failures.
