# Security & Hardening

## Overview

Security is an important part of the homelab environment.

The infrastructure uses multiple layers of security including Linux permissions, SSH administration, firewall controls, secure remote access, reverse proxy protection, and application security practices.

This project provides hands-on experience with securing Linux servers, protecting self-hosted services, managing access, and reducing unnecessary exposure.

---
## SSH Security

SSH is used for secure remote administration of the Ubuntu Server system.

The homelab uses SSH to manage the server without requiring direct console access.

Security practices include:

- Remote administration through SSH
- User-based access control
- Key-based authentication
- Avoiding unnecessary direct exposure to the internet

Useful SSH commands:

Check SSH service status:

```bash
systemctl status ssh
```


Restart SSH service:

```bash
sudo systemctl restart ssh
```


SSH provides secure administrative access while keeping management services separated from public applications.
## Firewall Hardening

### UFW Status

Ubuntu Server uses UFW (Uncomplicated Firewall) to manage host-based firewall rules.

Firewall verification:

```bash
sudo ufw status verbose
Status: active
Logging: on (low)

Default: deny (incoming), allow (outgoing), deny (routed)

To                         Action      From

22/tcp                     ALLOW IN    Anywhere
22/tcp (v6)                ALLOW IN    Anywhere (v6)
sudo ufw allow OpenSSH
sudo ufw status numbered
[ 1] 22/tcp      ALLOW IN    Anywhere
[ 2] 22/tcp (v6) ALLOW IN    Anywhere (v6)
sudo systemctl is-enabled ufw
enabled
systemctl status ufw --no-pager
Active: active (exited)

## System Updates & Patch Management

### Package Updates

Ubuntu package repositories are regularly refreshed to ensure the system receives current security and maintenance updates.

Update package information:

```bash
sudo apt update
73 packages can be upgraded.
apt list --upgradable
systemctl status unattended-upgrades --no-pager
Loaded: loaded (...; enabled; preset: enabled)
Active: active (running)
/etc/apt/apt.conf.d/50unattended-upgrades
${distro_id}:${distro_codename}
${distro_id}:${distro_codename}-security
test -f /var/run/reboot-required && echo "Reboot required" || echo "No reboot required"
No reboot required

