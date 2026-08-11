# Security & Hardening

## Overview

Security is an important part of the homelab environment.

The infrastructure uses multiple layers of security including Linux permissions, SSH hardening, firewall rules, automatic updates, and controlled service exposure.

This project provides hands-on experience with securing Linux servers, protecting self-hosted applications, and following basic infrastructure security practices.

---

# SSH Security

SSH is used for secure remote administration of the Ubuntu Server system.

The homelab uses SSH to manage the server without requiring direct console access.

Security practices include:

* Remote administration through SSH
* User-based access control
* Key-based authentication
* Avoiding unnecessary direct exposure to the internet
* Restricting access through firewall rules

## SSH Verification

Check SSH service status:

```bash
sudo systemctl status ssh
```

Restart SSH service after configuration changes:

```bash
sudo systemctl restart ssh
```

SSH access is protected by:

* Firewall restrictions
* User authentication
* Private network access
* Cloudflare Tunnel for public services instead of exposing SSH

---

### SSH Verification
SSH configuration was validated with `sudo sshd -t`.
The SSH service was reloaded and verified as active with `sudo systemctl reload ssh` and `sudo systemctl is-active ssh`.
A fresh SSH connection from Windows was successfully authenticated using an Ed25519 public key.
Password-based SSH authentication is no longer permitted.
# Firewall Hardening

Ubuntu Server uses UFW (Uncomplicated Firewall) to control host-based firewall rules.

The firewall follows the principle of:

* Deny unwanted incoming traffic
* Allow required services only
* Allow outgoing connections
* Prevent unauthorized network access

## Verify Firewall Status

The firewall was reviewed using:

```bash
sudo ufw status verbose
```

Verified configuration:

```text
Status: active
Logging: on (low)

Default: deny (incoming), allow (outgoing), deny (routed)

22/tcp                     ALLOW IN    Anywhere
22/tcp (v6)                ALLOW IN    Anywhere (v6)
```

## SSH Firewall Rule

SSH access is allowed through UFW:

```bash
sudo ufw allow OpenSSH
```

Verify firewall rules:

```bash
sudo ufw status numbered
```

Expected result:

```text
[ 1] 22/tcp      ALLOW IN    Anywhere
[ 2] 22/tcp (v6) ALLOW IN    Anywhere (v6)
```

## Firewall Service Verification

Confirm UFW starts automatically:

```bash
sudo systemctl is-enabled ufw
```

Result:

```text
enabled
```

Verify service status:

```bash
sudo systemctl status ufw --no-pager
```

Result:

```text
Active: active (exited)
```

---

# System Updates & Patch Management

Keeping the operating system updated is an important security practice.

Ubuntu package repositories are regularly checked for security updates and maintenance releases.

## Package Update Verification

Update package information:

```bash
sudo apt update
```

Check available upgrades:

```bash
apt list --upgradable
```

## Automatic Security Updates

The server uses unattended upgrades to automatically install approved security updates.

Verify service status:

```bash
systemctl status unattended-upgrades --no-pager
```

Verified:

```text
Loaded: loaded
Active: active (running)
```

Check installed version:

```bash
apt policy unattended-upgrades
```

Installed package:

```text
unattended-upgrades:
Installed: 2.12ubuntu9
```

## Test Automatic Updates

A dry run was performed:

```bash
sudo unattended-upgrade --dry-run --debug
```

Result:

```text
No packages found that can be upgraded unattended and no pending auto-removals

upgrade result: True
```

This confirms unattended upgrades are functioning correctly.

---

# Kernel and Reboot Management

After updates, verify whether the system requires a reboot:

```bash
test -f /var/run/reboot-required && echo "Reboot required" || echo "No reboot required"
```

Current result:

```text
No reboot required
```

---

# Service Exposure Management

Public services are not directly exposed through SSH or open firewall ports.

External access is provided through:

* Cloudflare Tunnel
* Reverse proxy services
* HTTPS encryption
* Authentication layers

Current security architecture:

```text
Internet
   |
Cloudflare Tunnel
   |
Nginx Proxy Manager
   |
Docker Services
   |
Ubuntu Server
   |
UFW Firewall
```

---

# Future Security Improvements

Planned improvements:

* Disable password-based SSH authentication
* Enable SSH key-only authentication
* Configure Fail2Ban
* Add regular security audits
* Implement centralized logging
* Add automated backup verification
* Document disaster recovery procedures

---

# Security Verification Checklist

Completed:

* [x] SSH enabled and verified
* [x] Firewall enabled
* [x] Incoming traffic restricted
* [x] SSH firewall rule configured
* [x] Automatic security updates enabled
* [x] Unattended upgrades tested
* [x] Reboot status verified

Future:

* [ ] SSH key-only authentication
* [ ] Fail2Ban deployment
* [ ] Security monitoring
* [ ] Backup restore testing


## Firewall Hardening

The Ubuntu Server VM uses UFW (Uncomplicated Firewall) to control incoming and outgoing network traffic.

### UFW Configuration

UFW is enabled and configured with secure default policies:

    Status: active
    Logging: on (low)
    Default: deny (incoming), allow (outgoing), deny (routed)

### SSH Access

SSH access is explicitly permitted on TCP port 22:

    22/tcp       ALLOW IN    Anywhere
    22/tcp (v6)  ALLOW IN    Anywhere (v6)

The configured UFW rule is:

    ufw allow 22/tcp

### Verification

Firewall status was verified with:

    sudo ufw status verbose
    sudo ufw status numbered
    sudo ufw show added

Verified configuration:

- UFW is active.
- Incoming connections are denied by default.
- Outgoing connections are allowed by default.
- Routed traffic is denied by default.
- SSH access is allowed on TCP port 22.
- IPv4 and IPv6 SSH rules are present.
- UFW logging is enabled at the low level.

This configuration provides a basic firewall security layer while maintaining required SSH administration access.

## OpenMediaVault Firewall Audit

The OpenMediaVault server was audited as part of the homelab security hardening process.

### Firewall Baseline

The OpenMediaVault system does not use UFW. The installed firewall components include nftables and iptables.

The firewall configuration was verified with:

```bash
sudo nft list ruleset
sudo iptables -L -n -v
sudo omv-confdbadm read conf.system.network.iptables.rule --prettify
```

Verified baseline:

* nftables ruleset is empty.
* iptables contains no configured rules.
* OMV firewall configuration contains no configured rules.
* UFW is not installed.

### Network Configuration

The OpenMediaVault server uses:

```text
IP address: 192.168.1.137
Interface: ens18
Network: 192.168.1.0/24
Gateway: 192.168.1.1
```

### Services Audited

The following services were verified:

* SSH — TCP port 22
* OMV Web Administration — TCP port 80
* SMB — TCP ports 139 and 445
* NFS — disabled
* SSH root login — disabled in the effective SSH configuration
* SSH public-key authentication — enabled
* SSH TCP forwarding — disabled
* SSH compression — disabled

### Security Status

The OMV firewall baseline has been documented before implementing additional firewall rules. No firewall changes were made during this audit.

This provides a verified starting point for future OMV firewall hardening while avoiding disruption to SSH, web administration, and SMB services.
