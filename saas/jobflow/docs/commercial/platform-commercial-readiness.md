# Platform Commercial Readiness

Version: 1.0
Status: Pre-validation
Last updated: 2026-08-21
Owner: SaaS Platform

---

## 1. Purpose

This document is the authoritative commercial-readiness checklist for the shared SaaS platform.

It applies to:

- Platform commercialization
- Platform administration
- Platform authentication and tenancy
- Platform pilot billing
- Platform pilot lifecycle
- RenewalDesk
- JobFlow
- Future registered products

Legacy JobFlow commercial documents remain product-specific and must not be used as evidence that the shared platform or another product is commercially ready.

---

## 2. Governing Roadmap

Every product follows:

Build → Document → Demonstrate → Customer Validation → Package → Sell

A product may be technically complete without being commercially ready.

Platform capabilities support commercialization but do not prove:

- Customer demand
- Product value
- Willingness to pay
- Product-market fit
- Pricing validity
- Sales readiness

---

## 3. Readiness Levels

### Platform Foundation Ready

The shared technical and operational foundation exists.

### Product Demonstration Ready

A product can be shown using deployed software and a repeatable workflow.

### Customer Validation Ready

Discovery questions, evidence records, and demonstrations are prepared.

### Pilot Ready

A qualified lead, pilot agreement, billing decision, owner, tenant, and success criteria exist.

### Packaging Ready

Repeated evidence supports a defined offer and price hypothesis.

### Sales Ready

A validated offer, reliable onboarding, payment process, support process, and customer terms exist.

### Commercially Operating

Real customers are paying and the platform can reliably bill, support, renew, suspend, and offboard them.

---

## 4. Authoritative Platform Procedures

The current platform commercialization procedures are:

### Sales

`docs/commercial/platform-sales-process.md`

Defines:

- Lead stages
- Discovery
- Demonstration
- Qualification
- Pilot agreement
- Tenant conversion
- Packaging
- Selling

### Pilot Billing

`docs/commercial/platform-pilot-billing.md`

Defines:

- Free validation pilot
- Paid pilot
- Default $99 pricing hypothesis
- Stripe-hosted invoicing
- Payment confirmation
- Refunds
- Disputes
- Recurring-billing gate

### Pilot Lifecycle

`docs/commercial/platform-pilot-lifecycle.md`

Defines:

- Entry criteria
- Tenant provisioning
- Onboarding
- Support
- Check-ins
- Pilot review
- Suspension
- Reactivation
- Offboarding
- Retention

These procedures apply to every registered product.

---

## 5. Platform Technical Foundation

### Product Architecture

- [x] Products are registered with the platform
- [x] Leads are associated with products
- [x] Tenants are associated with products
- [x] Product workspaces remain product-owned
- [x] Product APIs remain product-owned
- [x] Product migrations are discoverable
- [x] Deployment uses product-aware migrations
- [x] Multiple products can operate on the shared platform

### Authentication and Authorization

- [x] User authentication exists
- [x] Secure cookie sessions exist
- [x] Tenant membership is enforced
- [x] Platform-operator authorization exists
- [x] Tenant isolation is tested
- [x] Suspended tenants are denied product access
- [ ] External security review completed
- [ ] Commercial penetration testing completed

### Tenant Administration

- [x] Tenants can be inspected
- [x] Memberships can be managed
- [x] Last-owner protections exist
- [x] Tenants can be suspended
- [x] Tenants can be reactivated
- [x] Tenant status is visible
- [x] Administrative actions are audited
- [ ] Tested tenant-deletion workflow exists
- [ ] Customer data-export workflow exists

### Commercialization

- [x] Public lead capture exists
- [x] Leads are product-specific
- [x] Lead lifecycle states exist
- [x] Qualification exists
- [x] Closing exists
- [x] Qualified leads can be provisioned
- [x] Tenant provisioning creates an owner membership
- [x] Conversion is linked to the provisioned tenant
- [x] Legacy conversion reconciliation exists
- [ ] Manual lead creation exists
- [ ] Follow-up scheduling exists
- [ ] Lead disposition reasons exist
- [ ] Lead notes exist
- [ ] Pilot records exist
- [ ] Billing state exists in the platform

Unchecked workflow features are not current blockers because lead volume and pilot evidence do not yet justify them.

---

## 6. Platform Operations

### Deployment

- [x] Production deployment exists
- [x] Product-aware migration process exists
- [x] API health checking exists
- [x] Web deployment exists
- [x] HTTPS access exists
- [x] Direct API exposure is restricted
- [x] Database exposure is restricted
- [x] Security headers exist
- [x] Rate limiting exists

### Backup and Recovery

- [x] Database backup procedure is documented
- [x] Restore procedure is documented
- [x] Restore validation has been performed
- [x] Recovery documentation exists
- [ ] Pilot-specific retention procedure has been exercised
- [ ] Tenant-specific export has been tested
- [ ] Tenant-specific deletion has been tested

### Monitoring

- [x] Infrastructure monitoring exists
- [x] Service availability monitoring exists
- [x] API health monitoring exists
- [ ] Commercial support alerting is defined
- [ ] Billing-event monitoring exists
- [ ] Pilot check-in reminders exist

Billing-event monitoring and pilot automation are intentionally deferred.

---

## 7. Platform Security Readiness

Completed foundations:

- [x] Authentication required for protected APIs
- [x] Platform administration requires operator access
- [x] Tenant boundaries are enforced
- [x] Secure cookie authentication is used
- [x] Frontend token storage was removed
- [x] Login rate limiting exists
- [x] Public lead rate limiting exists
- [x] Tenant suspension is enforced
- [x] Administrative audit logging exists
- [x] Database is not publicly exposed

Outstanding commercial controls:

- [ ] Formal security risk assessment
- [ ] Incident-response procedure exercised
- [ ] Customer-facing security statement
- [ ] Vulnerability disclosure channel
- [ ] Security contact defined
- [ ] External security assessment
- [ ] Customer breach-notification procedure reviewed
- [ ] Stripe webhook security design

Stripe webhook controls are deferred until provider integration is justified.

---

## 8. Platform Privacy and Data Readiness

Documented:

- [x] Public repository evidence should be anonymized
- [x] Payment credentials must remain outside the platform
- [x] Pilot suspension must preserve data
- [x] Initial 30-day pilot retention hypothesis exists
- [x] Deletion requires verified authority and an approved process

Not completed:

- [ ] Privacy policy
- [ ] Customer-facing data-handling statement
- [ ] Data-processing inventory
- [ ] Data retention policy legally reviewed
- [ ] Customer access-request process
- [ ] Customer deletion-request process
- [ ] Data export process
- [ ] Subprocessor list
- [ ] Geographic data-processing review
- [ ] Backup-retention alignment review

Do not claim legal privacy compliance from internal planning documents alone.

---

## 9. Platform Legal Readiness

Not completed:

- [ ] Business entity confirmed for commercial operation
- [ ] Terms of service prepared
- [ ] Privacy policy prepared
- [ ] Pilot agreement prepared
- [ ] Paid-pilot terms prepared
- [ ] Support terms prepared
- [ ] Acceptable-use policy prepared
- [ ] Limitation-of-liability terms reviewed
- [ ] Warranty disclaimers reviewed
- [ ] Intellectual-property terms reviewed
- [ ] External developer terms reviewed
- [ ] Data-processing terms reviewed
- [ ] Cancellation terms reviewed
- [ ] Refund terms reviewed
- [ ] Customer communication consent reviewed
- [ ] Professional legal review completed

Internal process documents do not replace professional legal advice.

Do not accept a paid commercial customer until minimum customer terms and business identity are ready.

---

## 10. Platform Billing Readiness

Documented:

- [x] Platform and product billing boundaries defined
- [x] JobFlow operational invoices separated from platform billing
- [x] Free validation-pilot policy defined
- [x] Paid-pilot procedure defined
- [x] Default $99 paid-pilot hypothesis defined
- [x] Payment-before-provisioning rule defined
- [x] Stripe-hosted invoice decision documented
- [x] Refund process documented
- [x] Dispute process documented
- [x] Recurring-subscription implementation gate defined

Not completed:

- [ ] Stripe account verified for live payments
- [ ] Stripe business identity configured
- [ ] Stripe payout account verified
- [ ] Stripe branding configured
- [ ] Stripe invoice template configured
- [ ] Stripe payment methods reviewed
- [ ] Stripe refund permissions reviewed
- [ ] Tax obligations reviewed
- [ ] First test invoice completed
- [ ] First live pilot invoice completed
- [ ] First live payment reconciled
- [ ] First refund tested
- [ ] Recurring price validated
- [ ] Subscription terms defined
- [ ] Platform billing integration implemented

Do not build subscription billing before the documented recurring-billing gate is met.

---

## 11. Platform Support Readiness

Documented:

- [x] Pilot support boundaries defined
- [x] Initial support availability defined
- [x] One-business-day ordinary response target defined
- [x] Severity levels defined
- [x] Security and isolation issues prioritized
- [x] Feature-request handling defined
- [x] Support evidence requirements defined

Not completed:

- [ ] Support email address designated
- [ ] Support intake tested with a real pilot
- [ ] Support response target exercised
- [ ] Incident escalation exercised
- [ ] Customer-facing support instructions published
- [ ] Support burden measured
- [ ] Repeated support issues analyzed
- [ ] Product support ownership exercised

The documented response targets are operating goals, not contractual service-level guarantees.

---

## 12. Platform Pilot Readiness

Documented:

- [x] Standard 30-day pilot defined
- [x] Free and paid pilot types defined
- [x] Entry criteria defined
- [x] Success-criteria guidance defined
- [x] Provisioning procedure defined
- [x] Onboarding procedure defined
- [x] Check-in cadence defined
- [x] Extension rules defined
- [x] Review procedure defined
- [x] Suspension procedure defined
- [x] Reactivation procedure defined
- [x] Offboarding procedure defined
- [x] Retention hypothesis defined
- [x] Implementation gate defined

Not completed:

- [ ] Real discovery interview completed
- [ ] Real product demonstration completed with a prospect
- [ ] Real lead qualified
- [ ] Real pilot agreement completed
- [ ] First validation pilot provisioned
- [ ] First onboarding completed
- [ ] First pilot check-in completed
- [ ] First pilot review completed
- [ ] First offboarding or paid continuation completed
- [ ] Pilot process updated from actual evidence

The platform is procedurally prepared for a pilot but has not proven the process operationally.

---

## 13. RenewalDesk Readiness

### Build

- [x] Tenant-scoped renewal management
- [x] Renewal dashboard
- [x] Urgency calculation
- [x] Search and filtering
- [x] Editing
- [x] Owner assignment
- [x] Owner email
- [x] Reminder queue
- [x] Reminder processing
- [x] Delivery tracking
- [x] SMTP delivery
- [x] Production email delivery verified

### Document

- [x] Customer validation plan
- [x] Interview record template
- [x] Demonstration flow
- [x] Platform sales process
- [x] Platform pilot billing procedure
- [x] Platform pilot lifecycle procedure

### Demonstrate

- [x] Internal production workflow demonstrated
- [ ] Demonstrated to a real prospect

### Customer Validation

- [ ] First discovery interview completed
- [ ] Five discovery conversations completed
- [ ] Three prospects independently report the problem
- [ ] Two prospects report meaningful consequences
- [ ] Two prospects agree to evaluate
- [ ] One real validation pilot completed
- [ ] Willingness-to-pay evidence recorded

### Package

- [ ] Validated target segment
- [ ] Validated core problem
- [ ] Validated core workflow
- [ ] Initial offer defined from evidence
- [ ] Pricing hypothesis tested
- [ ] Support burden measured

### Sell

- [ ] Customer-facing terms ready
- [ ] Billing setup ready
- [ ] Paid offer made
- [ ] First paid pilot completed
- [ ] Recurring offer validated
- [ ] First recurring customer acquired

Current RenewalDesk position:

**Demonstrate / Customer Validation**

Do not add speculative RenewalDesk features while validation is pending.

---

## 14. JobFlow Readiness

### Build

- [x] Core customer-to-payment workflow exists
- [x] Multi-tenant foundation exists
- [x] Production deployment exists
- [x] Public customer request exists
- [x] Platform product integration exists

### Document

- [x] Product definition exists
- [x] Customer discovery plan exists
- [x] Business model hypothesis exists
- [x] Platform sales process applies
- [x] Platform pilot billing procedure applies
- [x] Platform pilot lifecycle procedure applies

### Demonstrate

- [x] Internal end-to-end workflow demonstrated
- [ ] Current workflow demonstrated to a real prospect

### Customer Validation

- [ ] First completed discovery interview recorded
- [ ] Target segment validated
- [ ] Problem severity validated
- [ ] Willingness to pilot validated
- [ ] Willingness to pay validated

### Package and Sell

- [ ] Validated package
- [ ] Validated price
- [ ] Customer terms
- [ ] Paid pilot
- [ ] Recurring customer

Current JobFlow position:

**Customer Validation pending**

Do not confuse technical maturity with commercial validation.

---

## 15. Future Product Readiness

Every future product must complete:

### Build

- [ ] Product registered
- [ ] Product-owned models
- [ ] Product-owned migrations
- [ ] Product-owned API
- [ ] Product workspace
- [ ] Tenant isolation tests
- [ ] Demonstrable MVP

### Document

- [ ] Product definition
- [ ] Target customer hypothesis
- [ ] Problem hypothesis
- [ ] Validation plan
- [ ] Demonstration flow
- [ ] Pilot success criteria

### Demonstrate

- [ ] Internal demonstration
- [ ] Prospect demonstration

### Customer Validation

- [ ] Discovery evidence
- [ ] Problem evidence
- [ ] Alternative analysis
- [ ] Pilot interest
- [ ] Willingness-to-pay evidence

### Package

- [ ] Validated offer
- [ ] Validated scope
- [ ] Initial price hypothesis
- [ ] Support boundaries

### Sell

- [ ] Customer terms
- [ ] Billing readiness
- [ ] Paid pilot
- [ ] Recurring offer
- [ ] Commercial customer

A new product must not skip directly from Build to Sell.

---

## 16. Evidence Rules

Mark an item complete only when objective evidence exists.

Acceptable evidence includes:

- Committed documentation
- Passing automated tests
- Production verification
- Recorded customer interview
- Demonstration notes
- Pilot agreement
- Stripe invoice
- Confirmed payment
- Pilot usage record
- Pilot review
- Customer decision

Unacceptable evidence includes:

- Hypothetical customer answers
- Internal enthusiasm
- Technical completion alone
- Unsent outreach messages
- Planned interviews
- Unverified payment claims
- Assumed legal compliance
- Features built without customer need

---

## 17. Premature Work Flags

The following work is premature now:

- Custom Stripe API integration
- Subscription database tables
- Automated payment webhooks
- Customer billing portal
- Multiple pricing tiers
- Usage-based billing
- Broad paid advertising
- Large sales campaigns
- Complex CRM features
- Automated pilot lifecycle
- Tenant deletion automation
- Product feature expansion without evidence

Allowed work includes:

- Security fixes
- Data-integrity fixes
- Demonstration blockers
- Customer discovery
- Prospect demonstrations
- Evidence recording
- Pilot preparation
- Real pilot support
- Documentation corrections
- Operational verification

---

## 18. Readiness Decision

### Platform

Current status:

**Foundation and procedures ready; commercial operation unvalidated**

### RenewalDesk

Current status:

**Demonstration and customer validation**

### JobFlow

Current status:

**Customer validation pending**

### Billing

Current status:

**Manual pilot procedure documented; live billing untested**

### Legal

Current status:

**Planning only; customer-facing documents and professional review incomplete**

### Support

Current status:

**Procedure documented; real pilot operation untested**

---

## 19. Single Next Milestone

Complete one real RenewalDesk customer discovery interview and product demonstration.

Completion criteria:

- Actual prospect participates
- Current renewal workflow is recorded
- Problem severity is recorded
- Existing alternatives are recorded
- RenewalDesk is demonstrated
- Positive and negative evidence are recorded
- Pilot interest is recorded
- Willingness-to-pay evidence is recorded
- Platform lead status reflects the evidence
- No personal information is committed publicly

No other commercialization milestone should replace this until it is completed or evidence supports changing the product direction.
