# Platform Pilot Lifecycle Procedure

Version: 1.0
Status: Initial operating procedure
Last updated: 2026-08-21
Owner: SaaS Platform

---

## 1. Purpose

This document defines the shared platform process for onboarding, operating, reviewing, and closing customer pilots.

It applies to:

- RenewalDesk
- JobFlow
- Future registered products
- Products developed under the platform developer contract

The platform owns the common pilot lifecycle.

Each product supplies its product-specific workflow, demonstration, success criteria, and usage evidence.

---

## 2. Pilot Lifecycle

The standard lifecycle is:

Qualified Lead
→ Pilot Agreement
→ Billing Decision
→ Tenant Provisioning
→ Owner Verification
→ Product Onboarding
→ Pilot Operation
→ Pilot Review
→ Continue, Convert, Suspend, or Close

The commercial roadmap remains:

Build → Document → Demonstrate → Customer Validation → Package → Sell

Provisioning a tenant does not prove customer validation or create a paid customer.

---

## 3. Architectural Ownership

### Platform Responsibilities

The platform owns:

- Lead qualification
- Product assignment
- Pilot authorization
- Billing decision
- Tenant provisioning
- Initial owner membership
- Authentication
- Tenant lifecycle
- Platform access
- Operator administration
- Audit records
- Shared support intake
- Pilot review process
- Offboarding coordination

### Product Responsibilities

Each product owns:

- Product-specific onboarding
- Product workflow
- Product documentation
- Pilot use case
- Pilot success criteria
- Product usage evidence
- Product-specific support guidance
- Product defects
- Product data

### Customer Responsibilities

The pilot participant owns:

- Providing accurate pilot information
- Assigning an accountable owner
- Protecting login credentials
- Using the product for the agreed purpose
- Reporting problems
- Participating in review conversations
- Providing honest feedback
- Following agreed data-handling boundaries

---

## 4. Standard Pilot Terms

Default pilot structure:

- Duration: 30 calendar days
- Products: One product
- Tenants: One tenant
- Initial owners: One
- Standard onboarding: Included
- Pilot review: Required
- Automatic renewal: Disabled
- Custom development: Excluded
- Production guarantee: Not offered
- Continuous availability guarantee: Not offered
- Data export: Best effort where supported
- Extension: Requires an explicit decision

A different duration requires a documented reason.

Do not create open-ended pilots.

---

## 5. Pilot Types

### Free Validation Pilot

Purpose:

- Validate the problem
- Observe real workflow use
- Gather evidence
- Identify defects and workflow gaps

Default:

- No charge
- 30 days
- One initial validation pilot per product
- Narrow use case
- Required pilot review

### Paid Pilot

Purpose:

- Test willingness to pay
- Test onboarding and support effort
- Test purchasing and billing
- Validate continuing value

Default:

- $99 one-time pricing hypothesis
- 30 days
- Payment before provisioning
- No automatic renewal
- Standard onboarding
- Required pilot review

The paid-pilot amount is a hypothesis, not final pricing.

---

## 6. Entry Criteria

A pilot may begin only when:

- The lead belongs to the correct product
- Discovery has occurred
- A meaningful problem was identified
- The product is relevant
- A pilot owner is identified
- The owner has an active user account
- A use case is defined
- Success criteria are written
- Start and end dates are agreed
- Support boundaries are understood
- Billing requirements are satisfied
- The lead is marked `qualified`

Do not provision a tenant only because a prospect requests access.

---

## 7. Pilot Agreement Record

Before provisioning, record privately:

- Anonymized customer reference
- Lead ID
- Product ID
- Product name
- Pilot type
- Pilot owner
- Billing contact when applicable
- Tenant name
- Proposed tenant slug
- Pilot start date
- Pilot end date
- Primary use case
- Data to be entered
- Success criteria
- Check-in dates
- Support contact
- Billing status
- End-of-pilot review date

Do not commit customer personal information, billing information, or confidential business data to the public repository.

---

## 8. Success Criteria

Every pilot requires measurable success criteria.

Good success criteria describe behavior or outcomes.

Examples:

- The customer enters at least five real records
- The customer completes the core workflow
- The customer uses the product during at least two weeks
- A reminder or workflow event is successfully delivered
- The customer can complete the workflow without operator intervention
- The customer reports a specific reduction in effort or risk
- The customer asks to continue using the product

Weak success criteria include:

- The customer likes the interface
- The demonstration went well
- The customer was interested
- The software remained online
- The tenant was provisioned

Technical operation is necessary but does not establish customer value.

---

## 9. Billing Gate

### Free Pilot

Before provisioning:

- Pilot type is confirmed as free
- No invoice is created
- The customer understands the pilot has no automatic continuation
- Learning obligations are agreed

### Paid Pilot

Before provisioning:

- Price is agreed
- Stripe invoice is sent
- Stripe shows the invoice as paid
- Product and customer match the qualified lead
- Pilot dates are confirmed

Do not provision a paid pilot from:

- A pending payment
- A payment screenshot
- A customer statement
- An unverified email
- A client-side payment claim

Follow `platform-pilot-billing.md`.

---

## 10. User Readiness

Before tenant provisioning, confirm:

- The pilot owner has a platform user account
- The user account is active
- The email address is verified operationally
- The owner can access the platform sign-in page
- The owner understands credential security
- The owner has not shared a password
- The owner can receive required product communications

Do not create shared user accounts.

Each person requiring access should eventually have an individual account and membership.

---

## 11. Tenant Provisioning

Provision through platform commercialization.

Procedure:

1. Open the commercialization workspace.
2. Locate the qualified lead.
3. Verify the product.
4. Verify the business or tenant name.
5. Select the initial owner.
6. Review the generated tenant slug.
7. Confirm the slug is unique and appropriate.
8. Provision the tenant.
9. Confirm the lead becomes `converted`.
10. Confirm the tenant is `active`.
11. Confirm the owner membership exists.
12. Open tenant administration.
13. Verify the product and owner.
14. Record the provisioning result privately.

Do not manually create unrelated database records to bypass the platform workflow.

---

## 12. Provisioning Verification

After provisioning, verify:

- Tenant ID exists
- Tenant product is correct
- Tenant status is `active`
- Tenant slug is correct
- Initial owner is correct
- Owner membership role is `owner`
- Owner user is active
- Product workspace loads
- Tenant isolation is effective
- Other tenant data is not visible
- Product API requests succeed
- Audit evidence exists where applicable

If any check fails, stop onboarding and fix the provisioning defect.

---

## 13. Product Access Handoff

Send the owner:

- Product name
- Product URL
- Sign-in URL
- Tenant ID or approved tenant selection instructions
- Pilot start date
- Pilot end date
- Primary pilot use case
- Support contact
- Check-in date
- Review date
- Security reminder

Do not send:

- Passwords
- Session tokens
- API secrets
- SMTP credentials
- Database credentials
- Another customer’s tenant information

---

## 14. Initial Onboarding Session

Default onboarding duration:

30 minutes.

Agenda:

1. Confirm the participant’s role.
2. Restate the pilot problem.
3. Confirm success criteria.
4. Confirm pilot dates.
5. Sign in.
6. Open the correct product workspace.
7. Confirm the correct tenant.
8. Complete one realistic product workflow.
9. Explain how to report problems.
10. Confirm the next check-in.
11. Avoid demonstrating unrelated features.
12. Ask the participant to perform the next action.

The participant should operate the product during onboarding.

An operator-only demonstration is not onboarding.

---

## 15. Product-Specific Onboarding

Each product must define:

- Core workflow
- Minimum pilot data
- Required fields
- Expected product event
- Success criteria
- Known limitations
- Support boundaries
- End-of-pilot evidence

### RenewalDesk Example

Minimum onboarding workflow:

1. Create a real or realistic renewal.
2. Set the renewal date.
3. Add the category and vendor.
4. Assign an owner.
5. Add an owner email.
6. Configure reminder lead time.
7. Confirm urgency status.
8. Edit the renewal.
9. Confirm search and filtering.
10. Observe reminder delivery when the date qualifies.

### JobFlow Example

Minimum onboarding workflow:

1. Create a customer.
2. Create a job.
3. Create and progress an estimate.
4. Schedule the job.
5. Complete the work.
6. Create an invoice.
7. Record payment.
8. Confirm final workflow status.

Product onboarding examples do not change platform pilot rules.

---

## 16. Support Model

Pilot support is a shared platform responsibility with product-specific investigation.

Initial support channel:

- Direct operator email or agreed customer communication channel

Initial support availability:

- Monday through Friday
- Normal business hours in Eastern Time
- No 24-hour support commitment

Response target:

- Acknowledge ordinary pilot issues within one business day
- Prioritize security, access, data-isolation, and complete outage reports
- Provide updates when resolution requires additional time

These are operating targets, not contractual service-level guarantees.

---

## 17. Support Classification

### Severity 1 — Critical

Examples:

- Suspected cross-tenant data exposure
- Unauthorized access
- Credential compromise
- Complete product outage affecting the pilot
- Destructive data corruption

Action:

- Acknowledge as soon as practical
- Protect access and data first
- Suspend affected access when necessary
- Preserve evidence
- Investigate before resuming normal use

### Severity 2 — High

Examples:

- Pilot owner cannot sign in
- Core product workflow is blocked
- Required reminder or workflow event fails
- Significant incorrect data behavior

Action:

- Investigate during the current or next business day
- Provide a workaround only if safe
- Determine whether pilot dates need adjustment

### Severity 3 — Normal

Examples:

- Usability confusion
- Minor display issue
- Non-blocking defect
- Documentation question
- Feature suggestion

Action:

- Record and evaluate
- Do not promise implementation
- Address when justified by pilot goals

---

## 18. Support Evidence

For every material pilot issue, record privately:

- Date reported
- Product
- Tenant reference
- Reporter
- Severity
- Observed behavior
- Expected behavior
- Reproduction evidence
- Workaround
- Resolution
- Time impact
- Whether success criteria were affected
- Whether the issue indicates a product or platform defect

Do not place sensitive customer data in public issue descriptions.

---

## 19. Feature Requests

When a participant requests a feature:

1. Ask what problem the feature would solve.
2. Ask how the problem is handled today.
3. Ask how often the problem occurs.
4. Ask what happens if it remains unsolved.
5. Record the request as evidence.
6. Compare it with other interviews and pilots.
7. Do not promise a delivery date.

Implement only when:

- It fixes a demonstrated defect
- It protects security or data integrity
- It blocks the agreed pilot workflow
- It represents a repeated validated need
- Commercial evidence justifies the work

---

## 20. Pilot Check-In Cadence

Default 30-day schedule:

### Day 0 — Onboarding

- Confirm access
- Complete first workflow
- Confirm success criteria

### Day 3 — Access Check

- Confirm the owner can sign in
- Confirm initial data was entered
- Resolve access problems

### Day 7 — Early Workflow Review

- Review first-week usage
- Identify blockers
- Clarify workflow questions
- Avoid expanding scope

### Day 14 — Midpoint Review

- Review progress against success criteria
- Identify product value or lack of value
- Record support burden
- Confirm the participant is still engaged

### Day 21 — Continuation Signal

- Ask whether the participant expects to continue
- Discuss missing requirements
- Identify purchase authority
- Prepare for final review

### Day 30 — Pilot Review

- Evaluate success criteria
- Review actual usage
- Record positive and negative evidence
- Discuss willingness to pay
- Decide the tenant’s next lifecycle state

Do not create automated check-in software until pilot volume justifies it.

---

## 21. Pilot Monitoring

During the pilot, monitor only information necessary for:

- Availability
- Security
- Support
- Agreed success criteria
- Product usage evidence
- Reminder or workflow delivery
- Error diagnosis

Do not silently expand data collection.

Do not treat infrastructure metrics as customer-value evidence.

Platform health and customer value are different measurements.

---

## 22. Mid-Pilot Changes

A pilot may be adjusted when:

- A demonstrated defect blocks progress
- Pilot dates were materially affected
- The agreed workflow requires clarification
- A security measure requires action

Do not change:

- Product scope
- Price
- Tenant ownership
- Data-handling terms
- Success criteria

without documenting and communicating the change.

---

## 23. Pilot Extension

Default rule:

No automatic extension.

An extension may be approved when:

- A platform outage materially reduced the pilot
- A blocking defect prevented evaluation
- The participant remained engaged
- A specific unresolved success criterion requires more time
- A defined commercial decision is pending

Default extension:

- Up to 14 additional days
- One extension
- No additional scope
- Written end date
- Scheduled final review

Repeated extensions indicate an unclear pilot or weak buying signal.

---

## 24. Pilot Review

At the final review, evaluate:

### Workflow Evidence

- Was real or realistic data entered?
- Was the core workflow completed?
- How often was the product used?
- Did the participant operate it without assistance?

### Problem Evidence

- Was the original problem real?
- Was it frequent or costly?
- Did existing alternatives remain preferable?
- Did the product reduce effort or risk?

### Product Evidence

- What worked?
- What failed?
- What was confusing?
- Which requested capabilities were repeated elsewhere?
- What support was required?

### Commercial Evidence

- Does the participant want continued access?
- Would the participant pay?
- What price or billing period was discussed?
- Who approves a purchase?
- What prevents a purchase?

### Operational Evidence

- Was onboarding repeatable?
- Was support manageable?
- Were security and reliability acceptable?
- Did the pilot require custom work?

---

## 25. Pilot Outcomes

Choose one outcome.

### Continue Discovery

Use when:

- Evidence remains insufficient
- The participant was not representative
- The problem requires more interviews
- No clear value was established

### Extend Pilot

Use only under the extension rules.

### Convert to Paid

Use when:

- Success criteria were met
- The participant wants continued access
- Value was demonstrated
- Price and terms are agreed
- Billing can be performed safely

During the manual phase, continued paid access requires a new Stripe invoice or an approved paid offer.

### Suspend

Use when:

- The pilot ends without continued agreement
- Payment is required but not received
- The customer requests a pause
- Access should be preserved temporarily

### Close

Use when:

- The problem is not meaningful
- The product is not suitable
- The participant declines
- The prospect becomes unresponsive
- The pilot fails without reason to continue

### Reconsider Product

Use when:

- Repeated evidence contradicts the product hypothesis
- Existing alternatives are consistently sufficient
- Required changes exceed the intended product boundary
- Support burden makes the product commercially impractical

---

## 26. Paid Continuation

Do not continue paid access automatically.

Before paid continuation:

- Pilot review is complete
- Customer value is documented
- Product scope is clear
- Price is agreed
- Billing period is agreed
- Support expectations are clear
- Cancellation expectations are clear
- Production readiness is acceptable
- Payment is confirmed

Until recurring subscriptions are implemented, paid continuation remains a manual platform process.

---

## 27. Tenant Suspension

Use platform administration to suspend a tenant when access should stop temporarily.

Before suspension:

1. Verify the tenant.
2. Verify the product.
3. Confirm the pilot outcome.
4. Notify the tenant owner when appropriate.
5. Record the reason privately.
6. Confirm no active billing agreement requires access.
7. Suspend through platform administration.
8. Verify protected tenant APIs return the expected denial.
9. Preserve data.

Suspension must not delete tenant data.

---

## 28. Tenant Reactivation

Reactivate when:

- A paid continuation is confirmed
- A valid extension is approved
- A suspension error is corrected
- A security issue is resolved
- The customer resumes under agreed terms

Before reactivation:

- Verify tenant identity
- Verify product
- Verify owner
- Verify billing state when applicable
- Confirm the new access period
- Reactivate through platform administration
- Verify owner access
- Record the decision privately

---

## 29. Pilot Offboarding

When a pilot ends without continuation:

1. Complete the pilot review.
2. Record the commercial outcome.
3. Notify the tenant owner.
4. Confirm the end date.
5. Suspend tenant access.
6. Preserve data during the retention window.
7. Identify any customer-requested export.
8. Remove unnecessary operator notes.
9. Review outstanding support or security issues.
10. Schedule the retention decision.

Do not immediately delete data after suspension.

---

## 30. Data Retention

Initial pilot retention decision:

- Suspend access at pilot end when continuation is not agreed
- Retain tenant data for 30 days
- Use the period to resolve continuation, export, or deletion requests
- Do not promise an export format that is not implemented
- Do not delete tenant data without identity verification and an approved deletion process
- Preserve legally or operationally required records separately when appropriate

Before the first real offboarding, verify the retention procedure against applicable legal, contractual, backup, and recovery requirements.

Backups may retain deleted data until normal backup expiration.

---

## 31. Data Deletion

Deletion is not part of routine pilot suspension.

A deletion request requires:

- Verified requester identity
- Verified tenant authority
- Confirmed tenant ID
- Confirmed product
- Review of legal and contractual retention needs
- Review of billing records
- Review of security or dispute holds
- Defined deletion scope
- Documented operator approval
- Verified completion

Do not perform direct database deletion casually.

A tested tenant-deletion workflow should be designed only when required.

---

## 32. Security Events

If a security issue occurs during a pilot:

1. Protect customer and platform data.
2. Restrict affected access.
3. Preserve logs and evidence.
4. Determine affected tenant and product scope.
5. Avoid speculation.
6. Communicate verified information.
7. Fix the issue before normal pilot activity resumes.
8. Review whether the pilot should be extended or ended.
9. Record lessons without exposing sensitive details.

Security work takes priority over pilot timelines.

---

## 33. Privacy Rules

Do not place the following in the public repository:

- Customer names
- Personal email addresses
- Phone numbers
- Billing addresses
- Invoice links
- Payment identifiers
- Tenant secrets
- Authentication data
- Confidential workflow details
- Raw interview transcripts without consent

Use anonymized identifiers such as:

- `Small Business Owner 001`
- `RenewalDesk Pilot 001`
- `JobFlow Pilot 001`

---

## 34. Pilot Evidence Record

Each completed pilot should record:

- Anonymized participant
- Product
- Segment
- Start and end dates
- Pilot type
- Use case
- Success criteria
- Workflows completed
- Usage evidence
- Problems identified
- Defects identified
- Requested capabilities
- Support effort
- Positive evidence
- Negative evidence
- Willingness-to-pay evidence
- Outcome
- Next action

Facts and interpretations must remain separate.

---

## 35. Platform Audit Expectations

Existing platform actions should use existing audit capabilities where available.

Important lifecycle actions include:

- Tenant provisioned
- Tenant suspended
- Tenant reactivated
- Membership changed
- Legacy conversion reopened

Future pilot automation should add audit events for:

- Pilot authorized
- Pilot started
- Pilot extended
- Pilot completed
- Paid continuation approved
- Offboarding initiated
- Retention decision completed

Do not add these database capabilities until real pilot operations justify them.

---

## 36. Product-Agnostic Requirement

No product may implement its own tenant onboarding, billing, suspension, or offboarding system when the shared platform already owns that lifecycle.

Every product must integrate through:

- Product registration
- Product-associated leads
- Platform tenant provisioning
- Platform membership
- Platform authentication
- Platform tenant lifecycle
- Platform commercialization
- Platform audit

Products may customize only their product-specific onboarding workflow and success criteria.

---

## 37. Current Product Application

### RenewalDesk

Current position:

- MVP deployed
- Reminder delivery verified
- Validation plan documented
- Interview 001 planned
- No completed interview
- No real pilot
- No validated pricing

Next allowed lifecycle action:

Complete discovery and demonstration before authorizing a pilot.

### JobFlow

Current position:

- MVP workflow implemented
- Platform tenant integration exists
- Customer validation remains incomplete
- Product billing is separate from JobFlow invoices

Next allowed lifecycle action:

Customer discovery before a new commercial pilot.

### Future Products

A future product must:

1. Register with the platform.
2. Define its MVP.
3. Document its target problem.
4. Complete a demonstration.
5. Gather discovery evidence.
6. Qualify a pilot.
7. Use this shared lifecycle.

---

## 38. Operator Checklist

### Before Provisioning

- [ ] Correct product confirmed
- [ ] Discovery completed
- [ ] Lead qualified
- [ ] Pilot owner active
- [ ] Use case documented
- [ ] Success criteria documented
- [ ] Pilot type confirmed
- [ ] Billing gate satisfied
- [ ] Start and end dates agreed
- [ ] Review scheduled

### After Provisioning

- [ ] Tenant created
- [ ] Product correct
- [ ] Tenant active
- [ ] Owner membership present
- [ ] Owner access verified
- [ ] Product workspace verified
- [ ] Tenant isolation verified
- [ ] Onboarding instructions sent
- [ ] First workflow completed
- [ ] Check-in scheduled

### During Pilot

- [ ] Day 3 access check
- [ ] Day 7 workflow review
- [ ] Day 14 midpoint review
- [ ] Day 21 continuation signal
- [ ] Support issues recorded
- [ ] Scope controlled
- [ ] Evidence separated from assumptions

### At Pilot End

- [ ] Success criteria reviewed
- [ ] Usage reviewed
- [ ] Customer feedback recorded
- [ ] Support burden reviewed
- [ ] Willingness to pay reviewed
- [ ] Outcome selected
- [ ] Tenant lifecycle action completed
- [ ] Retention decision scheduled
- [ ] Commercial evidence updated

---

## 39. Implementation Gate

Do not build automated pilot lifecycle features until:

- At least two real pilots are operated
- Manual tracking becomes unreliable
- Repeated lifecycle tasks are identified
- Required fields are validated
- Audit requirements are clear
- Retention requirements are reviewed
- Product differences are understood

Potential future platform capabilities include:

- Pilot records
- Pilot start and end dates
- Success criteria
- Check-in tasks
- Pilot status
- Billing state
- Product usage summaries
- Pilot review records
- Retention deadlines
- Operator alerts

These are future directions, not approved implementation work.

---

## 40. Roadmap Position

Current platform pilot-lifecycle position:

**Document**

The process is defined but has not been exercised with a real customer.

The next platform pilot milestone is:

Complete one real discovery interview and demonstration, then decide whether the lead qualifies for the first free validation pilot.

The next technical milestone should be selected only when:

- A demonstrated defect blocks the pilot
- A security or data-integrity issue requires action
- A repeated validated need appears
- Manual pilot operation proves a platform capability is necessary
