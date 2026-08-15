# JobFlow

JobFlow is a SaaS product experiment for independent home-service businesses.

## Current Phase

MVP prototype and customer validation.

## Problem Hypothesis

Small service businesses may manage customers, jobs, estimates, scheduling, and invoices across disconnected tools.

## MVP Workflow

Customer → Job → Estimate → Approval → Schedule → Complete → Invoice → Paid

## Implemented Features

- Customer records
- Job records
- Job status tracking
- Estimate creation
- Estimate approval/decline
- Job scheduling
- Start job workflow
- Job completion
- Invoice creation
- Invoice status tracking
- Send invoice
- Mark invoice paid
- Browser persistence using localStorage

## Prototype Workflow

### 1. Customer

Create a customer with:

- Name
- Phone
- Email
- Address

### 2. Job

Create a job associated with a customer.

Example:

> Website Setup

### 3. Estimate

Create an estimate associated with the job.

Example:

> Website setup and hosting — $300.00

### 4. Approval

Send the estimate and approve or decline it.

Approved estimates advance the associated job.

### 5. Scheduling

Schedule an approved job with:

- Date
- Time

### 6. Completion

Move the job through:

Scheduled → In Progress → Completed

### 7. Invoice

Create an invoice from a completed job.

Example:

> INV-0001 — $300.00

### 8. Payment

Move the invoice through:

Draft → Sent → Paid

## Validation Test

The prototype has been successfully tested with:

- Customer: Test Customer
- Job: Website Setup
- Estimate: $300.00
- Scheduled: August 20, 2026 at 10:00
- Invoice: INV-0001
- Final invoice status: Paid

## Technology

Current prototype:

- HTML
- CSS
- JavaScript
- Browser localStorage
- Python HTTP server for local demonstration

## Architecture

The current prototype is intentionally simple and disposable.

It does not yet use:

- Backend API
- Database
- Authentication
- Multi-user accounts
- Payments integration
- Email delivery
- Production deployment

## Validation Goal

The next phase is not to build a large application.

The goal is to demonstrate the workflow to prospective home-service businesses and determine whether the problem is real, frequent, painful, and valuable enough to pay to solve.

## Product Direction

Potential future capabilities may include:

- Customer portal
- Mobile-friendly job management
- Automated reminders
- Estimate PDF generation
- Invoice PDF generation
- Email notifications
- Online payments
- Authentication
- Multi-tenant accounts
- Reporting
- Backup and recovery

These features are hypotheses, not committed product requirements.

## Initial Business Hypothesis

JobFlow may eventually become a small-business SaaS product focused on simplifying customer, job, estimate, scheduling, and payment workflows for independent service providers.

The immediate objective is customer validation before significant production development.# JobFlow

JobFlow is a SaaS product experiment for independent home-service businesses.

## Current Phase

MVP prototype and customer validation.

## Problem Hypothesis

Small service businesses may manage customers, jobs, estimates, scheduling, and invoices across disconnected tools.

## MVP Workflow

Customer → Job → Estimate → Approval → Schedule → Complete → Invoice → Paid

## Implemented Features

- Customer records
- Job records
- Job status tracking
- Estimate creation
- Estimate approval/decline
- Job scheduling
- Start job workflow
- Job completion
- Invoice creation
- Invoice status tracking
- Send invoice
- Mark invoice paid
- Browser persistence using localStorage

## Prototype Workflow

### 1. Customer

Create a customer with:

- Name
- Phone
- Email
- Address

### 2. Job

Create a job associated with a customer.

Example:

> Website Setup

### 3. Estimate

Create an estimate associated with the job.

Example:

> Website setup and hosting — $300.00

### 4. Approval

Send the estimate and approve or decline it.

Approved estimates advance the associated job.

### 5. Scheduling

Schedule an approved job with:

- Date
- Time

### 6. Completion

Move the job through:

Scheduled → In Progress → Completed

### 7. Invoice

Create an invoice from a completed job.

Example:

> INV-0001 — $300.00

### 8. Payment

Move the invoice through:

Draft → Sent → Paid

## Validation Test

The prototype has been successfully tested with:

- Customer: Test Customer
- Job: Website Setup
- Estimate: $300.00
- Scheduled: August 20, 2026 at 10:00
- Invoice: INV-0001
- Final invoice status: Paid

## Technology

Current prototype:

- HTML
- CSS
- JavaScript
- Browser localStorage
- Python HTTP server for local demonstration

## Architecture

The current prototype is intentionally simple and disposable.

It does not yet use:

- Backend API
- Database
- Authentication
- Multi-user accounts
- Payments integration
- Email delivery
- Production deployment

## Validation Goal

The next phase is not to build a large application.

The goal is to demonstrate the workflow to prospective home-service businesses and determine whether the problem is real, frequent, painful, and valuable enough to pay to solve.

## Product Direction

Potential future capabilities may include:

- Customer portal
- Mobile-friendly job management
- Automated reminders
- Estimate PDF generation
- Invoice PDF generation
- Email notifications
- Online payments
- Authentication
- Multi-tenant accounts
- Reporting
- Backup and recovery

These features are hypotheses, not committed product requirements.

## Initial Business Hypothesis

JobFlow may eventually become a small-business SaaS product focused on simplifying customer, job, estimate, scheduling, and payment workflows for independent service providers.

The immediate objective is customer validation before significant production development.
