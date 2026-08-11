# Monitoring Stack

Prometheus and Grafana monitoring stack for the homelab environment.

## Components

| Service | Purpose |
|---|---|
| Prometheus | Metrics collection and time-series database |
| Grafana | Monitoring dashboards and visualization |
| Node Exporter | Linux host metrics |
| cAdvisor | Docker container metrics |

## Architecture

All monitoring services run in Docker and communicate through:

```text
monitoring Docker Network
```

## Access

| Service | URL |
|---|---|
| Grafana | http://server-ip:3000 |
| Prometheus | http://server-ip:9090 |

## Collected Metrics

### Host

- CPU usage
- Memory usage
- Disk usage
- Network activity

### Containers

- Container CPU usage
- Container memory usage
- Container status
- Network traffic

## Status

Monitoring stack operational.

Verified:

- Prometheus collecting metrics
- Grafana dashboards working
- Node Exporter reporting host metrics
- cAdvisor reporting Docker metrics
