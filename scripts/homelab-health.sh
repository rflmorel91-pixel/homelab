#!/usr/bin/env bash

set -u
LOGFILE="$HOME/homelab/logs/health-check.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")
log() {
    echo "$1" | tee -a "$LOGFILE"
}

exec > >(tee -a "$LOGFILE") 2>&1
echo "========================================"
echo "        HOMELAB HEALTH CHECK"
echo "========================================"
echo
if ping -c 1 -W 2 192.168.1.1 >/dev/null 2>&1; then
    echo "[ OK ] Network gateway"
else
    echo "[FAIL] Network gateway"
fi
if ping -c 1 -W 3 1.1.1.1 >/dev/null 2>&1; then
    echo "[ OK ] Internet connectivity"
else
    echo "[FAIL] Internet connectivity"
fi
if systemctl is-active --quiet docker; then
    echo "[ OK ] Docker service"
else
    echo "[FAIL] Docker service"
fi
if [ "$(docker ps -q | wc -l)" -gt 0 ]; then
    echo "[ OK ] Docker containers running"
else
    echo "[FAIL] No Docker containers running"
fi
if docker ps --format '{{.Names}}' | grep -qx 'nextcloud'; then
    echo "[ OK ] Nextcloud container"
else
    echo "[FAIL] Nextcloud container"
fi
if docker ps --format '{{.Names}}' | grep -qx 'vaultwarden'; then
    echo "[ OK ] Vaultwarden container"
else
    echo "[FAIL] Vaultwarden container"
fi
if docker ps --format '{{.Names}}' | grep -qx 'authentik'; then
    echo "[ OK ] Authentik container"
else
    echo "[FAIL] Authentik container"
fi
if docker ps --format '{{.Names}}' | grep -qx 'nginx-proxy-manager'; then
    echo "[ OK ] Nginx Proxy Manager"
else
    echo "[FAIL] Nginx Proxy Manager"
fi
if docker ps --format '{{.Names}}' | grep -qx 'uptime-kuma'; then
    echo "[ OK ] Uptime Kuma"
else
    echo "[FAIL] Uptime Kuma"
fi
if docker ps --format '{{.Names}}' | grep -qx 'cloudflared'; then
    echo "[ OK ] Cloudflare Tunnel"
else
    echo "[FAIL] Cloudflare Tunnel"
fi
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

if [ "$DISK_USAGE" -lt 80 ]; then
    echo "[ OK ] Disk usage: ${DISK_USAGE}%"
else
    echo "[WARN] Disk usage: ${DISK_USAGE}%"
fi
MEMORY_USAGE=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')

if [ "$MEMORY_USAGE" -lt 80 ]; then
    echo "[ OK ] Memory usage: ${MEMORY_USAGE}%"
else
    echo "[WARN] Memory usage: ${MEMORY_USAGE}%"
fi
if systemctl is-active --quiet ssh; then
    echo "[ OK ] SSH service"
else
    echo "[FAIL] SSH service"
fi
echo
echo "========================================"
echo "        HEALTH CHECK COMPLETE"
echo "========================================"
