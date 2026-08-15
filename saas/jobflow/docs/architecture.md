# JobFlow v2 Architecture

## Purpose

JobFlow is a small SaaS application for independent home-service businesses.

The goal of v2 is to move the disposable browser prototype toward a real application with persistent data, a backend API, and a production-oriented architecture.

## Core Workflow

Customer → Job → Estimate → Approval → Schedule → In Progress → Completed → Invoice → Sent → Paid

## High-Level Architecture

```text
Browser
   |
   v
Web Application
   |
   v
Backend API
   |
   v
Database
```

The application is separated into three primary layers:

1. Frontend
2. Backend API
3. Persistent database

The frontend is responsible for the user experience. The backend owns business logic and validation. The database provides persistent storage.

## Architecture Goals

JobFlow v2 is designed to provide:

- Persistent application data
- Backend business logic
- REST API
- Authentication
- Authorization
- Relational database storage
- Automated testing
- Docker-based deployment
- CI/CD
- Monitoring
- Security
- Documentation
- A foundation for future multi-tenant SaaS operation

## Domain Model

### User

A user represents an authenticated person who can access the JobFlow application.

Typical fields include:

- ID
- Name
- Email
- Password or authentication identifier
- Role
- Created timestamp
- Updated timestamp

### Customer

A customer represents the person or business receiving services.

Typical fields include:

- ID
- Name
- Email
- Phone
- Address
- Notes
- Created timestamp
- Updated timestamp

A customer may have multiple jobs.

### Job

A job represents a service request or project for a customer.

Typical fields include:

- ID
- Customer ID
- Title
- Description
- Status
- Scheduled date
- Created timestamp
- Updated timestamp

### Estimate

An estimate represents the proposed cost of a job.

Typical fields include:

- ID
- Job ID
- Status
- Subtotal
- Tax
- Total
- Created timestamp
- Updated timestamp

### Estimate Line Item

Each estimate can contain multiple line items.

Typical fields include:

- ID
- Estimate ID
- Description
- Quantity
- Unit price
- Line total

Estimate totals should be calculated by the backend rather than trusted from client input.

### Schedule

A schedule represents when work is planned.

Typical fields include:

- ID
- Job ID
- Start time
- End time
- Notes

### Invoice

An invoice represents the bill generated for completed work.

Typical fields include:

- ID
- Job ID
- Invoice number
- Status
- Subtotal
- Tax
- Total
- Issued date
- Due date
- Created timestamp

### Payment

A payment records money received against an invoice.

Typical fields include:

- ID
- Invoice ID
- Amount
- Payment date
- Payment method
- Reference

Payment information should be treated as server-controlled financial data.
## Workflow and State Model

JobFlow uses explicit workflow states to control the lifecycle of a job from creation through payment.

```text
Customer
   |
   v
Job Created
   |
   v
Estimate Created
   |
   v
Estimate Sent
   |
   v
Customer Approval
   |
   v
Job Scheduled
   |
   v
In Progress
   |
   v
Completed
   |
   v
Invoice Created
   |
   v
Invoice Sent
   |
   v
Payment Received
   |
   v
Paid
```

### Job Statuses

The job lifecycle uses the following primary states:

- New
- Estimate
- Approved
- Scheduled
- In Progress
- Completed
- Invoiced
- Paid

### Estimate Statuses

Estimate records use explicit states:

- Draft
- Sent
- Approved
- Rejected

### Invoice Statuses

Invoice records use the following lifecycle:

- Draft
- Sent
- Paid

### State Transition Rules

Workflow transitions should be controlled by the backend.

The frontend may display available actions, but it must not be trusted to enforce business rules.

Examples include:

- A job cannot be scheduled without an appropriate estimate or approval.
- A job cannot be marked paid without an invoice.
- An invoice must belong to a valid job.
- A payment must belong to a valid invoice.
- Invalid workflow transitions must be rejected by the API.
## API Architecture

The frontend communicates with the backend through a versioned HTTP API.

The API is responsible for authentication, authorization, validation, business logic, and persistence.

```text
Browser
   |
   v
Web Application
   |
   v
HTTP API
   |
   v
Backend Services
   |
   v
Database
```

### API Base Path

The initial API uses a versioned path:

```text
/api/v1
```

Versioning provides a clear boundary for future API changes without immediately breaking existing clients.

### Core Resources

The API is organized around the primary JobFlow resources:

- Customers
- Jobs
- Estimates
- Schedules
- Invoices
- Payments
- Authentication

### Example Endpoints

```text
GET    /api/v1/customers
POST   /api/v1/customers
GET    /api/v1/customers/:id
PUT    /api/v1/customers/:id
DELETE /api/v1/customers/:id

GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/:id
PUT    /api/v1/jobs/:id

GET    /api/v1/estimates
POST   /api/v1/estimates
GET    /api/v1/estimates/:id
PUT    /api/v1/estimates/:id

GET    /api/v1/invoices
POST   /api/v1/invoices
GET    /api/v1/invoices/:id
PUT    /api/v1/invoices/:id
```

### Request Validation

Incoming API requests must be validated by the backend.

Validation should cover:

- Required fields
- Data types
- String lengths
- Email formats
- Numeric ranges
- Dates and times
- Resource relationships
- Workflow state transitions

### Response Format

API responses should use consistent JSON structures.

Errors should provide a predictable structure.

Example:

```json
{
  "error": "ValidationError",
  "message": "Customer name is required"
}
```

### HTTP Status Codes

The API should use standard HTTP status codes:

- 200 OK
- 201 Created
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 422 Unprocessable Entity
- 500 Internal Server Error
## Authentication and Authorization

Authentication establishes the identity of the user. Authorization determines what the authenticated user is allowed to access.

```text
Browser
   |
   v
Login
   |
   v
Authentication Service
   |
   v
Authenticated Session
   |
   v
Backend API
   |
   v
Authorization
   |
   v
Application Data
```

### Authentication Requirements

The application should support secure authentication for registered users.

Authentication requirements include:

- Secure password handling
- Protected sessions or tokens
- Logout and session invalidation
- Authentication required for protected API endpoints
- No authentication secrets stored in frontend source code

### Authorization

Authorization is enforced by the backend API.

The frontend may hide controls that a user cannot use, but the backend must independently verify every protected operation.

### Security Boundaries

The primary security boundaries are:

```text
Internet
   |
   v
HTTPS
   |
   v
Web Application
   |
   v
Authenticated API
   |
   v
Validated Business Logic
   |
   v
Database
```

The database should never be directly accessible from the public Internet.

### Secrets and Configuration

Secrets must be separated from application source code.

Examples include:

- Database credentials
- Application secret keys
- Authentication secrets
- API keys
- Production service credentials

Environment-specific configuration should be supplied through environment variables or a secure configuration system.

Real secrets must never be committed to GitHub.
## Database Architecture

The database is the system of record for JobFlow.

The application backend is the only component that should communicate directly with the database.

```text
Web Application
      |
      v
Backend API
      |
      v
Database
```

### Database Responsibilities

The database is responsible for persistent storage of:

- Users
- Customers
- Jobs
- Estimates
- Estimate line items
- Schedules
- Invoices
- Payments

### Relational Model

JobFlow uses relationships between business entities to maintain data integrity.

Primary relationships include:

```text
Customer 1 ---- N Job
Job      1 ---- N Estimate
Estimate 1 ---- N Estimate Line Item
Job      1 ---- N Schedule
Job      1 ---- N Invoice
Invoice  1 ---- N Payment
```

Foreign keys should be used to maintain valid relationships between records.

### Data Integrity

Database constraints should protect critical relationships and values.

Examples include:

- Required fields
- Unique identifiers
- Foreign key constraints
- Valid numeric values
- Valid timestamps
- Unique invoice numbers

### Migrations

Database schema changes should be managed through versioned migrations.

Migrations should be committed to Git and applied consistently across development and production environments.

The application should never depend on manually editing production database tables.

### Persistence

Application containers should be considered replaceable.

Persistent data must survive:

- Container restarts
- Container replacement
- Application deployments
- Host restarts

Database storage must therefore use persistent volumes or managed database storage.

### Backup Requirements

Database backups are a critical recovery requirement.

Backups should include:

- Complete database data
- Database schema and migrations
- Required application configuration

Backups should be tested through an actual restoration process rather than assumed to be valid.
## Deployment Architecture

JobFlow is designed to run as a containerized application.

The initial deployment target is a Linux server environment using Docker and Docker Compose.

```text
Internet
   |
   v
DNS / HTTPS
   |
   v
Reverse Proxy
   |
   v
Web Application
   |
   v
Backend API
   |
   v
Database
```

### Containerization

Application components should be packaged as containers where practical.

Containers provide:

- Consistent application environments
- Repeatable deployments
- Isolation between services
- Simplified development and testing
- Easier application upgrades

### Docker Compose

Docker Compose can be used to define the local and initial self-hosted application stack.

A typical deployment may contain:

- Web application container
- Backend API container
- Database container
- Reverse proxy

### Network Segmentation

Only services that need external access should be exposed publicly.

The preferred traffic flow is:

```text
Internet
   |
   v
HTTPS Reverse Proxy
   |
   v
Web/API Application
   |
   v
Internal Database Network
   |
   v
Database
```

The database should remain on an internal network and should not publish its database port directly to the Internet.

### Environment Separation

JobFlow should support separate environments for development, testing, and production.

Each environment should have its own configuration and database resources.

Production credentials must never be reused in development.

### Deployment Flow

The intended deployment flow is:

```text
Developer
   |
   v
Git Repository
   |
   v
CI Tests
   |
   v
Build Container Images
   |
   v
Deploy
   |
   v
Application Environment
```
## CI/CD and Automation

JobFlow should use automated validation and deployment workflows to reduce manual errors and provide repeatable releases.

### Continuous Integration

Every change submitted to the repository should be automatically validated before it is merged.

CI should perform:

- Source code formatting checks
- Static analysis
- Unit tests
- Integration tests
- API tests
- Frontend tests
- Build validation
- Container image build validation

### Continuous Delivery

Validated changes should be packaged into deployable artifacts.

The deployment process should be repeatable and should not require manually modifying application files on the server.

### GitHub Actions

GitHub Actions can provide the initial CI/CD platform for JobFlow.

A typical workflow is:

```text
Git Push
   |
   v
GitHub Actions
   |
   +---- Lint
   |
   +---- Test
   |
   +---- Build
   |
   +---- Security Checks
   |
   v
Container Image
   |
   v
Deployment
```

### Infrastructure Automation

Infrastructure should be managed separately from application code.

Terraform is the preferred infrastructure-as-code tool for supported infrastructure.

Infrastructure automation should provide:

- Repeatable provisioning
- Version-controlled infrastructure definitions
- Consistent environments
- Reduced manual configuration
- Documented infrastructure changes

### Release Strategy

Each application release should have a traceable Git commit or release identifier.

Production deployments should be associated with a known application version.

Failed deployments should have a documented rollback procedure.
## Observability and Monitoring

JobFlow should provide enough operational visibility to detect failures, investigate problems, and measure application health.

### Health Checks

The backend should expose a health endpoint that can be used by monitoring systems and deployment infrastructure.

Example:

```text
GET /api/v1/health
```

A healthy response confirms that the application is running and able to service requests.

### Application Logging

Application logs should provide useful information for troubleshooting without exposing sensitive data.

Logs should include:

- Timestamp
- Log level
- Service name
- Request or correlation identifier when available
- Relevant error information

Passwords, tokens, session secrets, and other sensitive credentials must never be written to logs.

### Metrics

The application should eventually expose operational metrics such as:

- Request count
- Request latency
- Error rate
- Authentication failures
- Database connection health
- Background job failures
- Resource utilization

### Monitoring Architecture

The intended monitoring flow is:

```text
JobFlow Application
       |
       +---- Logs
       |
       +---- Metrics
       |
       +---- Health Checks
       |
       v
Monitoring Platform
       |
       v
Alerts / Dashboard
```

### Alerting

Operational alerts should focus on actionable failures.

Examples include:

- Application unavailable
- Database unavailable
- High error rate
- Excessive response latency
- Failed deployments
- Storage capacity problems

Monitoring should support both proactive detection and post-incident troubleshooting.
## Scalability and Multi-Tenancy

JobFlow v2 should establish a foundation that can support multiple businesses without requiring a separate application codebase for each customer.

### Multi-Tenant Model

The initial SaaS architecture should use logical tenant isolation.

Each business is represented as a tenant.

```text
Platform
   |
   +---- Tenant A
   |       |
   |       +---- Customers
   |       +---- Jobs
   |       +---- Estimates
   |       +---- Invoices
   |
   +---- Tenant B
           |
           +---- Customers
           +---- Jobs
           +---- Estimates
           +---- Invoices
```

### Tenant Isolation

Business data must be isolated by tenant.

Every tenant-owned record should be associated with a tenant identifier.

The backend must enforce tenant boundaries on every request.

A user must never be able to access another tenant’s data by changing an identifier in an API request.

### Scalability Strategy

The initial architecture should favor simplicity while allowing individual components to scale independently later.

Potential scaling points include:

- Web application instances
- Backend API instances
- Background workers
- Database resources
- File or object storage

### Stateless Application Services

Application services should be designed to remain as stateless as practical.

Persistent state should be stored in appropriate external systems such as the database or object storage.

This allows additional application instances to be added without copying local application state.

### Future SaaS Growth

The architecture should allow future capabilities such as:

- Subscription plans
- Usage limits
- Tenant administration
- Billing integration
- Email notifications
- Customer portals
- Mobile applications
- Public API access
## Security Architecture

Security is treated as a cross-cutting concern across the frontend, API, database, infrastructure, and deployment pipeline.

### Application Security

The application should follow secure development practices including:

- Input validation
- Output encoding where appropriate
- Parameterized database queries
- Protection against common web vulnerabilities
- Secure authentication and authorization
- Secure session handling
- Rate limiting for sensitive endpoints
- Safe error handling

### API Security

API endpoints should be protected according to their sensitivity.

Security controls should include:

- Authentication on protected endpoints
- Authorization checks
- Request validation
- Rate limiting
- Appropriate HTTP security headers
- HTTPS for production traffic
- Controlled CORS configuration

### Database Security

Database access should be restricted to the backend application and authorized administrative operations.

Database credentials should use the minimum permissions required by the application.

Production database ports should not be exposed directly to the public Internet.

### Infrastructure Security

Production infrastructure should follow a least-privilege model.

Controls should include:

- Firewall rules
- Restricted management access
- Secure SSH configuration where applicable
- Operating system security updates
- Container image updates
- Secret management
- Backup and recovery procedures

### Supply Chain Security

Application dependencies and container images should be reviewed and kept up to date.

CI should identify known vulnerabilities where practical.

Dependencies should be pinned or version controlled where appropriate to improve build reproducibility.

### Security Incident Response

Security incidents should have a documented response process.

The process should include:

- Identify
- Contain
- Investigate
- Remediate
- Recover
- Document

Security events should be reviewed after remediation to identify improvements to the architecture and controls.
## Testing and Reliability

JobFlow v2 should use multiple levels of automated testing to protect business workflows and prevent regressions.

### Testing Layers

The testing strategy should include:

- Unit tests
- API tests
- Integration tests
- Database tests
- Frontend tests
- End-to-end workflow tests
- Security tests

### Unit Testing

Unit tests should verify individual business rules and application components in isolation.

Examples include:

- Estimate total calculations
- Invoice calculations
- Workflow transition validation
- Authorization rules
- Input validation

### Integration Testing

Integration tests should verify that application components work correctly together.

Examples include:

- API to database operations
- Authentication flows
- Customer creation and retrieval
- Job and estimate relationships
- Invoice and payment relationships

### End-to-End Testing

End-to-end tests should verify the complete business workflow from the user perspective.

The primary workflow is:

```text
Customer
   → Job
   → Estimate
   → Approval
   → Schedule
   → In Progress
   → Completed
   → Invoice
   → Sent
   → Paid
```

### Reliability Requirements

The application should fail safely and provide useful diagnostic information when failures occur.

Important reliability practices include:

- Database transactions for critical operations
- Idempotent operations where appropriate
- Graceful error handling
- Health checks
- Timeouts for external services
- Retry handling where appropriate
- Database backups
- Tested restoration procedures
- Documented recovery procedures

### Recovery

Recovery procedures should be documented for application, database, and infrastructure failures.

## Architecture Decisions

The following decisions define the initial direction of JobFlow v2.

### Backend-First Business Logic

Business rules belong in the backend rather than the browser.

This provides a consistent source of truth and prevents clients from bypassing workflow and authorization rules.

### API-Driven Design

The frontend communicates with the backend through an API rather than accessing the database directly.

This creates a clear boundary between presentation, business logic, and persistence.

### Relational Database

A relational database is appropriate for JobFlow because the application contains strongly related business entities such as customers, jobs, estimates, invoices, and payments.

### Containerized Deployment

Docker provides a consistent and repeatable deployment model across development, testing, and production environments.

### Infrastructure as Code

Terraform provides a path toward repeatable infrastructure provisioning and reduces dependence on manual infrastructure configuration.

### Version-Controlled Documentation

Architecture, infrastructure, deployment, and operational documentation should be maintained alongside the application source code.

Documentation changes should be reviewed and committed through the same Git workflow as application changes.

## Future Evolution

JobFlow v2 establishes the foundation for future product development.

Potential future capabilities include:

- Customer self-service portal
- Online estimate approval
- Online payments
- Automated email and SMS notifications
- Recurring jobs
- Calendar integration
- File and photo attachments
- Mobile application
- Subscription billing
- Usage-based billing
- Advanced reporting
- Audit logging
- Public API
- Third-party integrations

Future capabilities should be added without compromising the core separation between frontend, backend, database, and infrastructure.

## Architecture Summary

JobFlow v2 is designed as a containerized, API-driven SaaS application with persistent relational storage.

The architecture separates presentation, business logic, persistence, infrastructure, and operational concerns.

The system is designed around the complete service lifecycle:

Customer → Job → Estimate → Approval → Schedule → In Progress → Completed → Invoice → Sent → Paid

The architecture provides a foundation for secure deployment, automated testing, infrastructure automation, monitoring, and future multi-tenant SaaS growth.

## Document Status

Architecture version: JobFlow v2

Status: Initial architecture definition

This document should evolve as implementation decisions are made and validated.
