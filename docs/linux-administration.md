# Linux Administration

## Overview

Linux administration is a core part of the homelab environment.

The Ubuntu Server system is used to host Docker, networking services, monitoring, authentication, and self-hosted applications.

This project provides hands-on experience with Linux command-line administration, system services, users, permissions, networking, storage, troubleshooting, and system recovery.

---

## Systemd Service Management

Systemd is used to manage Linux services.

The homelab uses systemd to manage services that must start automatically and remain available after system reboots.

Services verified in the homelab include:

- Docker
- Cloudflare Tunnel

Both services have been verified as enabled at boot.
## Docker Service

Docker is the primary container platform used by the homelab.

Docker is configured to start automatically when Ubuntu Server boots.

The Docker service was verified with:

systemctl is-enabled docker

The expected result is:

enabled

The current service state was verified with:

systemctl is-active docker

The expected result is:

active
## Cloudflare Tunnel Service

Cloudflare Tunnel provides secure external access to selected homelab services.

The Cloudflare Tunnel service is managed by systemd and configured to start automatically after a reboot.

The service was verified with:

systemctl is-enabled cloudflared

The expected result is:

enabled

The current service state was verified with:

systemctl is-active cloudflared

The expected result is:

active

This configuration was validated during the homelab power outage recovery test.

## System Information Commands

Linux administration requires understanding the operating system, hardware resources, and running processes.

Useful commands used in the homelab include:

Check operating system information:

hostnamectl

Check CPU information:

lscpu

Check memory usage:

free -h

Check disk usage:

df -h

Check running processes:

top

These commands are used during troubleshooting, resource checks, and system maintenance.
## Storage and Filesystem Administration

Linux storage management is used to maintain application data, Docker volumes, and NAS services.

The homelab uses Linux storage concepts including:

- Virtual disks
- Filesystems
- Mount points
- Disk usage monitoring
- Persistent application storage

Useful storage commands:

List block devices:

lsblk

Check mounted filesystems:

mount

Display filesystem usage:

df -h

Display directory sizes:

du -sh <directory>

Storage troubleshooting is performed by verifying available disk space, filesystem status, and application data locations.
## Users, Permissions, and SSH Administration

Linux user and permission management is required for secure system administration.

The homelab uses SSH for remote administration of the Ubuntu Server system.

Useful commands:

Check current user:

whoami

Display logged-in users:

who

Change file ownership:

chown

Change file permissions:

chmod

Check SSH service status:

systemctl status ssh

SSH administration allows remote management without requiring direct console access.

## Package Management

Ubuntu Server uses the APT package manager to install, update, and maintain software.

Useful commands:

Update package information:

sudo apt update

Upgrade installed packages:

sudo apt upgrade

Install a package:

sudo apt install curl<package>

Remove a package:

sudo apt remove curl<package>

Package management is used for maintaining the operating system and installing required server software.
## Logs and Troubleshooting

Linux logs are essential for diagnosing service failures, startup problems, and system issues.

The homelab uses logs to troubleshoot:

- Docker services
- System services
- Network connectivity
- Application problems
- Startup failures

Useful commands:

View system logs:

journalctl

View logs for a specific service:

journalctl -u docker<service><service><service>

View recent system errors:

journalctl -p err

Follow live service logs:

journalctl -f

Reviewing logs is a key part of troubleshooting Linux servers.

