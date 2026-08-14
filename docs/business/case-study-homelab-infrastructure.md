# Homelab Infrastructure Case Study

## Overview

This project demonstrates the design, deployment, security, monitoring, automation, and documentation of a small self-hosted IT infrastructure environment.

The environment was built as a practical infrastructure laboratory and portfolio project to demonstrate capabilities that can be applied to small businesses, home-based businesses, remote workers, and small offices.

The overall approach was:

**Build → Secure → Monitor → Automate → Verify → Document**

---

## Project Objectives

The project was designed to develop and demonstrate practical skills in:

* Linux server administration
* Virtualization
* Storage management
* Networking
* Docker infrastructure
* Security hardening
* Monitoring and observability
* Backup and disaster recovery
* Infrastructure as Code
* CI/CD validation
* Infrastructure documentation
* Repeatable operational procedures

---

## Infrastructure Environment

### Physical Host

The primary virtualization host is a Dell OptiPlex 5060.

**Hardware:**

* Intel Core i5-8500 @ 3.00 GHz
* 6 CPU cores
* 16 GB DDR4 memory
* 2666 MT/s memory speed
* Approximately 1 TB physical storage

**Software:**

* Proxmox VE 9.2.5
* Debian GNU/Linux 13 (Trixie)
* KVM/QEMU
* LVM-thin storage

The compact physical platform provides sufficient resources for multiple infrastructure workloads while remaining suitable for continuous hands-on experimentation.

---

## Virtualization

Proxmox VE provides the virtualization layer for the environment.

Virtualized workloads include:

* Ubuntu Server
* OpenMediaVault
* Docker-based services
* Monitoring services
* Infrastructure automation workloads

The environment demonstrates practical VM lifecycle management including:

* VM creation
* CPU and memory allocation
* Virtual disk configuration
* SCSI storage
* VirtIO networking
* ISO management
* Linux VM administration
* Troubleshooting

---

## Linux Server & Docker Infrastructure

An Ubuntu Server VM hosts the primary Docker environment.

Docker and Docker Compose are used to deploy and manage multiple applications and infrastructure services.

Services demonstrated include:

* Nextcloud
* Vaultwarden
* Authentik
* Nginx Proxy Manager
* Uptime Kuma
* Immich
* Prometheus
* Grafana
* Node Exporter
* cAdvisor
* Cloudflared
* Portainer
* Stirling PDF

The environment demonstrates container deployment, persistent storage, networking, service configuration, troubleshooting, and operational management.

---

## Storage Infrastructure

OpenMediaVault was deployed as a virtual machine on Proxmox.

The NAS environment includes:

* OpenMediaVault 8.3.1
* Debian GNU/Linux 13
* Dedicated storage disk
* EXT4 filesystem
* SMB/CIFS file sharing
* Windows client access

Storage administration included filesystem configuration, mount management, SMB configuration, and access verification.

---

## Network & Remote Access

The infrastructure operates on a private IPv4 network.

Remote application access was implemented using Cloudflare Tunnel.

The architecture provides external access without requiring traditional inbound port forwarding.

The remote-access workflow includes:

```text
Internet
    ↓
Cloudflare
    ↓
Cloudflare Tunnel
    ↓
Ubuntu Server
    ↓
Docker
    ↓
Application Services
```

Nginx Proxy Manager provides reverse-proxy functionality where applicable.

---

## Security Hardening

Security was treated as a core part of the infrastructure rather than an afterthought.

Implemented security practices include:

* SSH configuration review
* SSH key-based authentication
* Root login restrictions
* UFW firewall configuration
* Secure firewall defaults
* User and access review
* Security update configuration
* Service exposure review
* OpenMediaVault SSH hardening
* OpenMediaVault firewall auditing

The security workflow is:

**Assess → Harden → Verify → Document**

Security configuration and verification procedures are maintained in version-controlled documentation.

---

## Monitoring & Observability

A monitoring and observability stack was deployed to provide visibility into infrastructure and application health.

Components include:

* Prometheus
* Grafana
* Node Exporter
* cAdvisor
* Uptime Kuma

Monitoring workflows include:

```text
Linux Host
    ↓
Node Exporter
    ↓
Prometheus
    ↓
Grafana
```

and:

```text
Docker Host
    ↓
cAdvisor
    ↓
Prometheus
    ↓
Grafana
```

Uptime Kuma provides service availability monitoring.

A Bash-based health-check script also performs automated checks for infrastructure and application health.

---

## Backup & Disaster Recovery

AWS was used to validate a complete backup and recovery workflow.

An EC2 instance was protected using AWS Backup.

The resulting recovery point was restored into a new EC2 instance.

The restored instance reached the `running` state and was subsequently terminated as part of controlled recovery-test cleanup.

The demonstrated workflow was:

```text
EC2
 ↓
AWS Backup
 ↓
Recovery Point
 ↓
Restore
 ↓
Validation
 ↓
Cleanup
```

This demonstrates practical experience with backup configuration, recovery-point validation, controlled restoration, recovery verification, and cleanup.

---

## Infrastructure as Code

Terraform was introduced to automate and manage Proxmox infrastructure through the Proxmox API.

The Terraform environment includes:

* Terraform 1.15.8
* bpg/proxmox provider
* Proxmox API authentication
* Parameterized VM configuration
* Reusable Terraform modules
* Infrastructure validation
* Git-based configuration management

Terraform was used to manage and provision Proxmox virtual machines.

The infrastructure workflow is:

```text
Terraform
    ↓
Proxmox API
    ↓
Reusable VM Module
    ↓
Parameterized VM Configuration
    ↓
VM Deployment
    ↓
Validation
```

---

## CI/CD Validation

GitHub Actions was added to the Terraform workflow.

The CI pipeline validates Terraform configuration on pushes to `main` and pull requests.

Validation includes:

* Terraform initialization
* Terraform formatting
* Terraform validation
* Terraform version consistency

The workflow intentionally does not automatically modify Proxmox infrastructure.

Infrastructure changes are reviewed locally with `terraform plan` before being applied.

This provides a safer separation between:

**Code Validation → Infrastructure Review → Infrastructure Deployment**

---

## Documentation & Version Control

The entire project is maintained as a version-controlled infrastructure portfolio.

Git and GitHub are used to track:

* Infrastructure documentation
* Terraform configuration
* Docker configuration
* Security documentation
* Monitoring documentation
* Operational procedures
* Business service packages

Changes are validated before being committed and synchronized with the remote repository.

The repository provides an auditable history of infrastructure development and operational improvements.

---

## Operational Automation

A Bash health-check script was developed to provide repeatable infrastructure validation.

The checks include:

* Network gateway availability
* Internet connectivity
* Docker service status
* Docker container status
* Application availability
* Disk usage
* Memory usage
* SSH service status

Health-check results can be logged for later review.

This demonstrates the use of simple automation to reduce repetitive operational checks.

---

## Results

The completed environment demonstrates an end-to-end infrastructure lifecycle:

```text
Plan
 ↓
Deploy
 ↓
Configure
 ↓
Secure
 ↓
Monitor
 ↓
Automate
 ↓
Backup
 ↓
Recover
 ↓
Validate
 ↓
Document
```

The project progressed from a basic virtualization host into a documented infrastructure environment containing:

* Virtualized servers
* NAS storage
* Containerized applications
* Remote-access infrastructure
* Security controls
* Monitoring
* Backup and recovery
* Infrastructure as Code
* CI validation
* Operational automation

---

## Business Value

The project demonstrates capabilities relevant to practical small-business infrastructure engagements.

Potential customer outcomes include:

* Reliable Linux server deployment
* Virtual machine deployment
* Docker application deployment
* NAS and file-service configuration
* SSH and firewall hardening
* Infrastructure monitoring
* Backup configuration
* Recovery testing
* Proxmox administration
* Terraform automation
* Infrastructure documentation

The emphasis is on delivering infrastructure that is:

**Reliable → Secure → Observable → Repeatable → Documented**

---

## Related Services

The capabilities demonstrated by this project support the following packaged services:

* Server & Infrastructure Setup
* Backup & Disaster Recovery
* Monitoring & Alerting
* Linux Security Hardening
* Virtualization & Infrastructure Automation

Each service is designed as a clearly scoped engagement with defined deliverables, verification, documentation, and client handoff.

---

## Project Status

**Status: Operational**

The homelab continues to serve as a practical infrastructure laboratory, portfolio, and testing environment for developing and demonstrating IT infrastructure services.

---

## Key Takeaway

This project demonstrates that infrastructure work is more than simply deploying servers.

A professional infrastructure engagement requires:

**Assessment → Implementation → Security → Monitoring → Automation → Verification → Documentation**

That lifecycle is the foundation of the services offered through this portfolio.
