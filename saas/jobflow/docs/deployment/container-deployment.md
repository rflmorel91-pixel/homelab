# JobFlow Container Deployment Validation

Version: 1.0

---

# Block 1 — Docker API Container

## Purpose

This document records the validated Docker deployment process for the JobFlow backend API.

## Container Architecture

Current deployment:

```text
Browser / LAN Client
        |
        |
JobFlow API Container
        |
        |
PostgreSQL Container
```

---

# Block 3 — Docker Compose Deployment Validation

## Unified Application Stack

JobFlow was validated using the root Docker Compose configuration with both application services managed as one stack:

```text
Docker Compose
    |
    +-- jobflow-api
    |     FastAPI / Uvicorn
    |     Host port 8001
    |
    +-- jobflow-db
          PostgreSQL 16
          Localhost port 127.0.0.1:5433
```

---

# Block 4 — PostgreSQL Backup and Restore Validation

## Backup Validation

A PostgreSQL custom-format backup was created from the live JobFlow database using `pg_dump`.

The backup archive was verified with `pg_restore --list`.

The archive contained the expected JobFlow database objects, including:

- alembic_version
- customers
- jobs
- estimates
- schedules
- invoices
- payments
- users
- tenants
- tenant_memberships

## Restore Validation

The backup was restored into a separate validation database:

```text
jobflow_restore_test
```

---

# Block 5 — Public HTTPS Validation

## Public Hostname

JobFlow was published through the existing Cloudflare Tunnel using:

```text
jobflow.fieldlookers.com
```

## Tunnel Routing

The Cloudflare Tunnel route forwards the public hostname to the internal JobFlow API:

```text
https://jobflow.fieldlookers.com
        |
        v
Cloudflare Tunnel
        |
        v
http://192.168.1.92:8001
        |
        v
jobflow-api
```

## DNS and HTTPS Validation

Public DNS resolution for `jobflow.fieldlookers.com` was verified through Cloudflare.

The public health endpoint was successfully tested:

```text
https://jobflow.fieldlookers.com/api/v1/health
```

Verified response:

```text
HTTP/2 200
```

```json
{
  "status": "healthy",
  "service": "jobflow-api"
}
```

The response identified Cloudflare as the public edge server.

## Authenticated Application Validation

JWT authentication was successfully performed through the public HTTPS hostname.

Tenant-scoped API access was then verified using a bearer token and the `X-Tenant-ID` header.

The public API successfully returned existing PostgreSQL-backed customer records.

## Validated Request Path

```text
Internet Client
    |
    v
HTTPS
    |
    v
jobflow.fieldlookers.com
    |
    v
Cloudflare Tunnel
    |
    v
JobFlow API
    |
    v
JWT Authentication
    |
    v
Tenant Authorization
    |
    v
PostgreSQL
```

Cloudflare Tunnel provides the public HTTPS termination and routing path for the JobFlow API.
