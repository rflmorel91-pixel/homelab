# Platform Module Boundaries

## Purpose

Reduce regression risk in large platform modules through small, behavior-preserving
extractions. This is not authorization for a broad rewrite, framework replacement, route
redesign, or aesthetic-only refactor.

Extraction should occur only when related product work next changes the affected area.

## Current concentration

The primary concentrated modules are:

- `backend/app/api/admin.py`: platform administration routes and mutations.
- `app/assets/admin-cac3598ae666.js`: administration state, rendering, API calls, event
  handling, authentication, billing, tenant, user, and audit behavior.
- `backend/app/products/workflow_automation/prospecting_api.py`: prospect qualification
  and outreach activity routes.
- `app/assets/prospecting-a1ff52b499b0.js`: prospecting operator interface behavior.

The administration HTML, JavaScript, and CSS are already separate assets. Future work
must preserve the current CSP-compatible external-asset structure.

## Backend administration boundaries

### Audit

Responsibilities:

- Administrative audit-log queries.
- Audit event serialization.
- Shared audit-event creation.

Dependencies:

- `AdminAuditLog`
- `User`
- SQLAlchemy session and query helpers
- Current platform operator dependency

Audit creation is used by multiple administrative mutations. It should not be moved until
all importers are identified and migrated together.

### Overview and directories

Responsibilities:

- Platform overview counts.
- Product, tenant, membership, and user directories.
- Product detail.
- Tenant and user detail responses.

Dependencies:

- `Product`
- `Tenant`
- `TenantMembership`
- `User`
- `Lead`

Existing response shapes are public contracts for the administration interface and must
remain unchanged.

### Tenant lifecycle and configuration

Responsibilities:

- Tenant suspension and reactivation.
- Tenant timezone updates.
- Tenant billing-account assignment.
- Associated audit events.

Dependencies:

- Tenant-context enforcement
- Billing models
- Audit creation
- Operator authorization

Tenant lifecycle extraction requires focused lifecycle and tenant-isolation tests in
addition to the full backend suite.

### Identity and membership

Responsibilities:

- User updates.
- Membership creation, role updates, and deletion.
- Platform-administrator controls.
- Associated audit events.

Dependencies:

- `User`
- `Tenant`
- `TenantMembership`
- Operator authorization
- Audit creation

All role restrictions and tenant-isolation behavior must remain unchanged.

### Billing

Responsibilities:

- Billing offer serialization and directory.
- Billing offer creation and updates.
- Billing account serialization and directory.
- Tenant billing configuration.

Dependencies:

- `BillingOffer`
- `BillingAccount`
- `Product`
- `Tenant`
- Operator authorization
- Audit creation

The existing `/api/v1/admin/billing` and `/api/v1/admin/billing/offers` routes and response
formats must remain unchanged.

## Frontend administration boundaries

### Core and authentication

Responsibilities:

- API base configuration.
- Escaping and status messages.
- Cookie-authenticated API requests.
- Operator sign-in, sign-out, and initialization.
- View navigation.

Authentication must remain cookie-only. No token storage may be introduced.

### Overview and directories

Responsibilities:

- Overview rendering.
- Product, client, validation-workspace, and user directories.
- Search and navigation into detail panels.

### Tenant detail

Responsibilities:

- Tenant rendering.
- Lifecycle actions.
- Timezone changes.
- Client activation invitations.
- Membership management.

### Identity and invitations

Responsibilities:

- User detail.
- Role and platform-administrator controls.
- User invitation creation and activation-link handling.

### Billing

Responsibilities:

- Billing directory rendering.
- Offer catalog rendering and editing.
- Tenant billing configuration.

### Activity

Responsibilities:

- Audit action labels.
- Audit-detail formatting.
- Administrative activity rendering.

Frontend extraction must preserve DOM IDs, event behavior, request paths, CSP compliance,
and current page URLs.

## Workflow Automation prospecting boundaries

### Campaigns and qualification

Responsibilities:

- Campaign creation and execution.
- Manual candidate creation.
- Campaign and candidate listings.
- Candidate review and qualification.

### Outreach activity

Responsibilities:

- Due follow-up listing.
- Initial outreach recording.
- Follow-up recording.
- Reply recording.
- Suppression and unsubscribe handling.
- Activity audit snapshots.

The status-transition, suppression, and audit rules are business controls and must remain
covered by focused tests.

## First low-risk extraction candidate

When billing work next modifies administration code, extract only:

- `billing_offer_data()`
- `billing_account_data()`

from `backend/app/api/admin.py` into a focused billing serialization module.

Why this is the first candidate:

- The functions have a cohesive serialization responsibility.
- They do not define routes.
- Moving them does not require router composition changes.
- Existing route paths and response formats can remain unchanged.
- Their model dependencies are narrow.
- Existing billing tests exercise their serialized output through the public API.

This document selects the candidate; it does not authorize an extraction before related
maintenance work requires it.

## Extraction rules

Every extraction must:

1. Begin from a clean branch synchronized with `origin/main`.
2. Be limited to one cohesive boundary.
3. Preserve API routes, status codes, response schemas, DOM IDs, and user-visible behavior.
4. Preserve cookie-only authentication, authorization, tenant isolation, audit creation,
   and CSP enforcement.
5. Avoid new frameworks and broad architectural rewrites.
6. Add or retain focused regression coverage for the affected boundary.
7. Run the full backend regression suite.
8. Run migration-head and migration-drift verification.
9. Run relevant frontend source, CSP, and production smoke checks.
10. Pass `git diff --check`.
11. Record the tested commit and deployment evidence before release.

If an extraction makes unrelated behavior changes, it must be split into a separate change.
