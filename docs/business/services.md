# IT Services

This document defines the initial IT services that can be offered based on the technologies and workflows demonstrated in the homelab environment.

## Service Philosophy

The service approach follows:

**Assess → Build → Secure → Monitor → Document**

The goal is to provide practical infrastructure services for small businesses, remote workers, and home users.

## Service 1 — Server & Infrastructure Setup

### Overview

Deploy and configure a reliable Linux-based server environment for applications, file services, internal tools, or other workloads.

### Services Included

- Linux server installation and configuration
- User and SSH configuration
- Firewall configuration
- Storage configuration
- Docker installation
- Docker Compose deployment
- Basic system hardening
- Service documentation
- Health verification

### Example Technologies

- Ubuntu Server
- Debian Linux
- Docker
- Docker Compose
- Proxmox

## Service 2 — Backup & Disaster Recovery

### Overview

Design and configure a backup strategy designed to protect important systems and provide a tested recovery process.

### Services Included

- Backup assessment
- Backup configuration
- Retention planning
- Backup verification
- Recovery testing
- Recovery documentation

### Demonstrated Capability

The homelab AWS environment includes a completed backup and restore validation:

`EC2 → AWS Backup → Recovery Point → Restore → Validation → Cleanup`

## Service 3 — Monitoring & Alerting

### Overview

Deploy monitoring and alerting so infrastructure problems can be detected before they become larger incidents.

### Services Included

- Server monitoring
- Container monitoring
- Resource monitoring
- Service availability monitoring
- Dashboard configuration
- Alert configuration
- Email notifications
- Health checks

### Example Technologies

- Prometheus
- Grafana
- Node Exporter
- cAdvisor
- Uptime Kuma
- CloudWatch
- SNS

## Service 4 — Security Hardening

### Overview

Establish a practical baseline security configuration for Linux servers and infrastructure.

### Services Included

- SSH hardening
- Firewall configuration
- User access review
- Root access restrictions
- Security update configuration
- Service exposure review
- Security documentation

### Example Technologies

- OpenSSH
- UFW
- Linux
- Cloud infrastructure security groups

## Service 5 — Virtualization & Infrastructure Automation

### Overview

Deploy repeatable infrastructure using virtualization and Infrastructure as Code.

### Services Included

- Proxmox configuration
- Virtual machine deployment
- VM templates
- Terraform configuration
- Infrastructure parameterization
- Infrastructure validation
- Git-based change tracking

### Example Technologies

- Proxmox VE
- Terraform
- Git
- GitHub
- bpg/proxmox provider

## Initial Target Customers

The initial target market includes:

- Small businesses
- Home-based businesses
- Remote workers
- Home users
- Small offices

## Business Goal

The initial business objective is to convert demonstrated technical capabilities into small, clearly defined service packages.

The first revenue milestone is:

**$1,000 in service revenue.**

Future packages can combine infrastructure setup, security, monitoring, backup, and documentation into fixed-scope offerings.
