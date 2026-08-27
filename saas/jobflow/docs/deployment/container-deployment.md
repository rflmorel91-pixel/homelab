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

JobFlow was validated using the root Docker Compose configuration with the application services managed as one stack:

```text
Docker Compose
    |
    +-- jobflow-web
    |     Nginx
    |     Internal port 80
    |     No host port publication
    |
    +-- jobflow-api
    |     FastAPI / Uvicorn
    |     Internal port 8001
    |     No host port publication
    |
    +-- jobflow-migrate
    |     Alembic migration service
    |     One-shot execution
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

The Cloudflare Tunnel route forwards the public hostname to the internal JobFlow web container:

```text
https://jobflow.fieldlookers.com
        |
        v
Cloudflare Tunnel
        |
        v
http://jobflow-web:80
        |
        v
jobflow-web
        |
        +-- / -> frontend
        |
        +-- /api/* -> jobflow-api:8001
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

### Browser login contract — issue #18

The updated browser login endpoint returns only
`{"status": "signed_in"}`. It does not return an access token or token type
in its JSON response.

Authentication uses the `jobflow_access_token` cookie with Secure, HttpOnly,
SameSite=Strict, Path=/, and a 30-minute lifetime. Logout deletes that cookie.
Browser requests use cookies; tenant selection stored in localStorage is
not an authentication credential.

Backend bearer-token support remains available for existing internal callers
and tests. The bearer verification above records historical deployment
evidence, not instructions to retrieve a token from browser login.

The release smoke-session helper uses a cookie jar and does not depend on
the login response body.

Verification on 2026-08-27:
- 50 focused authentication, security, password-reset, and invitation tests passed.
- Full backend suite: 556 tests passed.
- Migration drift check: no new upgrade operations detected.
- Git whitespace checks passed.

Exact-commit CI and production verification of this change remain pending.


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

Cloudflare Tunnel provides the public HTTPS termination and routes to the JobFlow web container over the internal Docker network. Nginx serves the frontend and proxies API requests internally to the JobFlow API.

---

# Block 6 — Frontend and Restart Resilience Validation

## Production Web Architecture

JobFlow now serves the browser frontend through a dedicated Nginx container.

The frontend uses the same-origin API path:

```text
/api/v1
```

Nginx proxies API requests internally to:

```text
http://jobflow-api:8001
```

The JobFlow API does not publish port 8001 directly to the host.

The validated public request path is:

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
jobflow-web:80
    |
    +-- / -> JobFlow static frontend
    |
    +-- /api/* -> jobflow-api:8001
                       |
                       v
                  PostgreSQL
```

## Container Services

The validated JobFlow Compose stack contains:

```text
jobflow-db
    PostgreSQL 16
    Host exposure: 127.0.0.1:5433

jobflow-migrate
    One-shot Alembic migration service
    Successful completion: Exited (0)

jobflow-api
    FastAPI / Uvicorn
    Internal container port: 8001
    No host port publication
    Docker healthcheck enabled

jobflow-web
    Nginx
    Internal container port: 80
    No host port publication
    Docker healthcheck enabled
```

## Frontend Health Validation

The Nginx frontend container includes a Docker healthcheck that verifies the local web server is responding.

Validated steady state:

```text
jobflow-db       healthy
jobflow-migrate  Exited (0)
jobflow-api      healthy
jobflow-web      healthy
```

## Controlled Restart Validation

A complete Docker Compose restart was performed.

After restart:

* PostgreSQL returned to healthy state.
* Alembic migrations completed successfully.
* The FastAPI container returned to healthy state.
* The Nginx frontend returned to healthy state.
* Public frontend access remained functional.
* Public API access remained functional.

Public frontend validation returned:

```text
https://jobflow.fieldlookers.com/
HTTP/2 200
Content-Type: text/html
```

Public API validation returned:

```text
https://jobflow.fieldlookers.com/api/v1/health
HTTP/2 200
```

with:

```json
{
  "status": "healthy",
  "service": "jobflow-api"
}
```

## Ubuntu Server Reboot Validation

The Ubuntu Server VM hosting JobFlow was rebooted to validate deployment persistence.

After the VM returned:

* Docker started successfully.
* `jobflow-db` restarted and became healthy.
* `jobflow-api` restarted and became healthy.
* `jobflow-web` restarted and became healthy.
* `cloudflared` restarted automatically.
* The public frontend returned HTTP 200.
* The public API health endpoint returned HTTP 200.

The long-running JobFlow containers and `cloudflared` use the following restart policy:

```text
unless-stopped
```

## Proxmox Startup Validation

The Ubuntu Server VM is configured to start automatically when the Proxmox host boots.

Verified Proxmox configuration:

```text
onboot: 1
```

This provides the validated recovery chain:

```text
Proxmox Host
    |
    v
Ubuntu Server VM
    |
    v
Docker
    |
    +-- jobflow-db
    +-- jobflow-api
    +-- jobflow-web
    +-- cloudflared
    |
    v
Public HTTPS JobFlow Service
```

## Validation Result

JobFlow has now been validated for:

* Internal Docker service-to-service routing
* Public HTTPS access through Cloudflare Tunnel
* Static frontend delivery through Nginx
* Same-origin API proxying
* JWT-authenticated application access
* PostgreSQL persistence
* Container health monitoring
* Controlled Docker Compose restart recovery
* Ubuntu Server reboot recovery
* Proxmox VM automatic startup
