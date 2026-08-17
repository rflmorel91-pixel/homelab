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
          Host port 5433

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
