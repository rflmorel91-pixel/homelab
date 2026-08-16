# JobFlow

JobFlow is a SaaS product experiment for independent home-service businesses.

The project began as a browser-based workflow prototype and is now being evolved into a database-backed web application using FastAPI and PostgreSQL.

## Current Phase

Backend integration and customer validation.

The original browser MVP demonstrated the complete proposed workflow:

**Customer → Job → Estimate → Approval → Schedule → In Progress → Completed → Invoice → Sent → Paid**

The current development phase is migrating that prototype from browser `localStorage` to a persistent backend architecture.

## Current Architecture

```text
Windows Browser
      |
      | HTTP
      v
JobFlow Frontend
192.168.1.92:8084
      |
      | REST API
      v
FastAPI Backend
192.168.1.92:8001
      |
      v
PostgreSQL
```

The application currently runs on the Ubuntu Server VM in the homelab.

## Technology Stack

### Frontend

* HTML
* CSS
* Vanilla JavaScript
* Fetch API
* Python HTTP server for development

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn

### Database

* PostgreSQL
* Alembic database migrations
* Separate test database for automated backend tests

### Development and Testing

* pytest
* Git
* GitHub
* Python virtual environment

## Backend API

The current backend implements persistent API resources for:

### Customers

* Create customer
* List customers
* Retrieve customer
* Update customer
* Delete customer

### Jobs

* Create job
* List jobs
* Retrieve job
* Update job
* Delete job
* Job status validation
* Job status transition enforcement

### Estimates

* Create estimate
* List estimates
* Retrieve estimate
* Update estimate
* Delete estimate
* Estimate status validation
* Estimate status transition enforcement

## Status Workflows

### Job Status

The backend controls valid job status values and transitions rather than relying on the browser to enforce workflow rules.

Job progression is tested through the backend test suite.

### Estimate Status

Estimate transitions are also enforced by the backend.

The frontend currently supports actions such as:

```text
Draft → Sent → Approved
             ↘ Declined
```

Invalid status values and invalid transitions are rejected by the API.

## Frontend Integration

The browser frontend now communicates with FastAPI instead of storing Customer, Job, and Estimate records in browser `localStorage`.

The frontend API base URL is:

```text
http://192.168.1.92:8001/api/v1
```

The current frontend provides:

* Customer creation
* Customer listing
* Job creation
* Job listing
* Estimate creation
* Estimate listing
* Estimate status actions
* API health indication
* API error messages
* Success messages
* HTML escaping for API-provided values

## Development Network Configuration

### JobFlow Frontend

```text
http://192.168.1.92:8084
```

Development server:

```bash
cd ~/homelab/saas/jobflow/app
python3 -m http.server 8084
```

### FastAPI Backend

```text
http://192.168.1.92:8001
```

Development server:

```bash
cd ~/homelab/saas/jobflow/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### API Health Check

Endpoint:

```text
GET /api/v1/health
```

Example:

```bash
curl http://192.168.1.92:8001/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "jobflow-api"
}
```

The frontend also checks this endpoint and displays the API health status.

## CORS

Because the frontend and backend use different ports, FastAPI uses `CORSMiddleware`.

The development frontend origin is:

```text
http://192.168.1.92:8084
```

This origin is explicitly allowed by the backend.

## Firewall Configuration

The Ubuntu Server uses UFW with inbound traffic denied by default.

JobFlow development access is restricted to the local LAN.

Frontend:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8084 proto tcp
```

Backend API:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8001 proto tcp
```

This permits JobFlow access from devices on the `192.168.1.0/24` network without exposing the development ports generally.

## Homelab Port Allocation

Existing services already occupy several nearby ports:

| Port | Service                 |
| ---- | ----------------------- |
| 8000 | Existing Docker service |
| 8001 | JobFlow FastAPI         |
| 8080 | Nextcloud               |
| 8081 | cAdvisor                |
| 8082 | Stirling PDF            |
| 8083 | WordPress               |
| 8084 | JobFlow frontend        |

The JobFlow frontend uses `8084` to avoid conflicts with existing homelab services.

## Database Migrations

Alembic manages the PostgreSQL schema.

Check whether model changes require a migration:

```bash
cd ~/homelab/saas/jobflow/backend
alembic check
```

Apply migrations:

```bash
alembic upgrade head
```

## Automated Tests

Backend tests are run with:

```bash
cd ~/homelab/saas/jobflow/backend
pytest -q
```

The automated suite covers Customer, Job, and Estimate API behavior, including workflow validation and invalid status transitions.

Before committing backend changes, the standard verification sequence is:

```bash
pytest -q
alembic check

cd ~/homelab/saas/jobflow
git diff --check
git status
```

## Original MVP

The original JobFlow browser prototype demonstrated:

* Customer records
* Job records
* Job status tracking
* Estimate creation
* Estimate approval and decline
* Job scheduling
* Start-job workflow
* Job completion
* Invoice creation
* Invoice status tracking
* Send invoice
* Mark invoice paid

The original prototype stored application state in browser `localStorage`.

That prototype proved the proposed workflow before backend development began.

## Current Backend Migration Scope

The database-backed implementation currently focuses on:

```text
Customer → Job → Estimate
```

The original scheduling, invoicing, and payment portions of the MVP have not yet been fully migrated into the current database-backed frontend.

This distinction is intentional: the original MVP validates the broader workflow while the current backend establishes the persistent application foundation.

## Validation Goal

JobFlow remains a product experiment.

The objective is to determine whether independent home-service businesses experience enough friction managing customers, jobs, estimates, scheduling, invoices, and payments to justify paying for a simpler integrated workflow.

Technical development should support that validation rather than replace it.

## Potential Future Capabilities

Potential future capabilities include:

* Scheduling persistence
* Invoice persistence
* Payment workflow
* Authentication
* Multi-tenant accounts
* Customer portal
* Mobile-friendly job management
* Automated reminders
* Estimate PDF generation
* Invoice PDF generation
* Email notifications
* Online payments
* Reporting
* Backup and recovery
* Production deployment

These remain product hypotheses rather than committed requirements.

## Project Principle

JobFlow development follows a simple progression:

**Prototype → Validate → Persist → Test → Integrate → Demonstrate → Validate with customers**

The goal is not to build unnecessary complexity. The goal is to create enough reliable software to test whether JobFlow solves a problem customers will pay to solve.
