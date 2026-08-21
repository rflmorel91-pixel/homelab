# Platform Sales Process

Version: 1.0
Status: Initial operating process
Last updated: 2026-08-21

---

## 1. Purpose

This document defines how the SaaS platform moves a prospect from initial interest to an active customer.

The process applies to every registered product while preserving product-specific positioning, validation evidence, demonstrations, pilots, and offers.

The platform sales sequence is:

Prospect → Discovery → Demonstration → Qualified Pilot → Provisioned Tenant → Pilot Evidence → Package → Sale

The governing roadmap is:

Build → Document → Demonstrate → Customer Validation → Package → Sell

A product must not be treated as commercially validated merely because it is technically complete or deployed.

---

## 2. Commercialization Principles

### Learn Before Selling

Early conversations should identify real customer problems before presenting features, pricing, or solutions.

### Demonstrate Working Software

Demonstrations should use deployed product functionality and realistic workflows.

Do not describe planned capabilities as available.

### Separate Interest from Evidence

Positive comments are not sufficient validation.

Stronger signals include:

- Describing a meaningful problem without prompting
- Reporting measurable consequences
- Sharing current workarounds
- Agreeing to test with real data
- Participating in a pilot
- Discussing a purchase decision
- Expressing willingness to pay

### Protect Product Focus

Do not implement a feature because one prospect mentions it.

Feature work should require:

- A demonstrated defect
- A security or data-integrity requirement
- A pilot-blocking requirement
- A repeated customer problem
- Strong supporting commercial evidence

### Keep Products Distinct

Each lead belongs to one registered product.

Discovery evidence, demonstrations, pilots, pricing, and conversion decisions must remain tied to that product.

Platform capabilities may support multiple products, but product progress must not be credited to another product.

---

## 3. Lead Status Definitions

The platform currently supports:

- `new`
- `contacted`
- `qualified`
- `converted`
- `closed`

These statuses have specific commercial meanings.

### New

Use when:

- A public lead is submitted
- A prospect is manually identified
- No meaningful outreach has occurred

Required next action:

- Review the lead
- Confirm the relevant product
- Send an initial discovery invitation

Do not mark a lead contacted merely because the record was viewed.

### Contacted

Use when:

- A discovery invitation has been sent
- Direct contact has occurred
- A conversation is being scheduled
- The prospect has responded

Required next action:

- Conduct discovery
- Record evidence
- Decide whether the lead meets qualification criteria

Contacted does not mean interested or qualified.

### Qualified

Use only when:

- A real problem has been discussed
- The product is relevant to that problem
- The prospect agrees to a demonstration, evaluation, or pilot
- A responsible person is identified
- There is a clear next action

For pre-validation products, qualification means qualified for learning or pilot participation—not necessarily qualified to purchase.

### Converted

Use only when:

- The lead is intentionally provisioned as a tenant
- An initial tenant owner is selected
- The prospect is entering an agreed pilot or customer onboarding
- The product association is correct

Tenant provisioning and conversion must occur together through the platform workflow.

Converted does not automatically mean paying customer.

### Closed

Use when:

- The prospect declines
- The problem is not meaningful
- The product is not relevant
- The prospect stops responding after reasonable follow-up
- Timing is unsuitable and no active next step exists
- The lead was invalid or duplicated

Record the reason outside the platform until structured disposition tracking is justified by lead volume.

Closed evidence is valuable and should influence positioning and targeting.

---

## 4. Sales Stages

### Stage 1 — Select Product and Target Segment

Before outreach, define:

- Product
- Target customer segment
- Problem hypothesis
- Expected workflow
- Reason the prospect may experience the problem
- Current validation status

Do not use a generic platform pitch.

Each prospect should be approached with a product-specific problem hypothesis.

### Stage 2 — Identify Prospect

A prospect should meet the current target-customer hypothesis.

Record:

- Business or organization
- Contact
- Relevant product
- Customer segment
- Contact method
- Reason for selection

Avoid collecting unnecessary personal information.

Use anonymized identifiers in public repository evidence.

### Stage 3 — Initial Outreach

The purpose of early outreach is to secure a discovery conversation.

The message should:

- Be brief
- Explain the problem area
- Request approximately 15 minutes
- Ask for honest feedback
- Avoid pressure
- Avoid unvalidated claims
- Avoid leading with pricing

After sending outreach:

- Move the lead from `new` to `contacted`
- Record the next action privately
- Follow up once if no response
- Close the lead if there is no engagement after reasonable follow-up

### Stage 4 — Customer Discovery

Conduct discovery before demonstrating the product.

Learn:

- Current process
- Current tools
- Responsible people
- Frequency of the task
- Problems and frustrations
- Consequences of failure
- Time or money involved
- Attempts to solve the problem
- Ability and authority to change the process

Record actual answers separately from interpretations.

Do not use hypothetical answers as customer evidence.

### Stage 5 — Demonstration

Demonstrate only after understanding the prospect’s current workflow.

A demonstration should:

- Remain under ten minutes
- Use deployed software
- Show one realistic workflow
- Connect features to problems already described
- Invite criticism
- Identify workflow mismatches
- Avoid promising unimplemented capabilities

End by asking:

- What would be useful?
- What would not fit?
- What is missing?
- Who would maintain the data?
- Would the prospect test with real information?

### Stage 6 — Qualification Decision

Mark the lead `qualified` only if evidence supports continued investment.

Qualification signals include:

- A meaningful problem exists
- Existing alternatives are insufficient
- Consequences or effort are identifiable
- The prospect sees relevance in the demonstrated workflow
- The prospect agrees to a defined next step
- A suitable pilot owner exists

Do not qualify solely because the prospect was polite or liked the interface.

If the evidence is weak:

- Continue discovery with other prospects, or
- Close the lead with a documented reason

### Stage 7 — Pilot Agreement

Before provisioning a tenant, agree on:

- Pilot product
- Pilot participant
- Pilot owner
- Data to be entered
- Workflow to be tested
- Pilot duration
- Success criteria
- Check-in schedule
- Data-handling expectations
- End-of-pilot decision

Keep the pilot narrow.

Do not provide unlimited custom development.

### Stage 8 — Tenant Provisioning

Provision only qualified leads.

The platform operator should:

1. Confirm the correct product.
2. Confirm the lead is qualified.
3. Select the initial tenant owner.
4. Choose a valid tenant slug.
5. Provision the tenant through commercialization.
6. Confirm product access.
7. Confirm the owner can sign in.
8. Record the pilot start.

Provisioning changes the lead to `converted`.

Converted means operationally onboarded, not commercially validated.

### Stage 9 — Pilot Operation

During the pilot, observe:

- Whether the participant enters real data
- Frequency of product use
- Whether the core workflow is completed
- Problems encountered
- Support required
- Workarounds abandoned or retained
- Evidence of saved time, reduced risk, or improved control
- Whether the participant asks to continue

Fix demonstrated defects.

Defer speculative enhancements unless they block the agreed pilot outcome.

### Stage 10 — Pilot Review

At the end of the pilot, review:

- Success criteria
- Actual usage
- Customer-reported value
- Missing requirements
- Support burden
- Security or reliability concerns
- Willingness to continue
- Willingness to pay
- Purchase authority and process

Possible outcomes:

- Continue customer discovery
- Extend the pilot with specific goals
- Package the product
- Offer a paid subscription
- Revise the target segment
- Close the opportunity
- Reconsider the product hypothesis

### Stage 11 — Package

Packaging begins only after customer evidence supports it.

Define:

- Target segment
- Core problem
- Core workflow
- Included capabilities
- Support boundaries
- Onboarding process
- Pilot-to-paid transition
- Initial price hypothesis
- Billing period
- Cancellation approach

Avoid multiple tiers until customer evidence demonstrates distinct buying needs.

### Stage 12 — Sell

A product is ready for active selling when:

- The problem has been repeatedly validated
- The MVP supports the validated workflow
- Demonstrations are repeatable
- At least one real pilot has been completed
- Value and willingness-to-pay evidence exist
- Onboarding is reliable
- Support expectations are defined
- Security and production risks are acceptable

The sales conversation should connect:

Problem → Consequence → Validated Workflow → Demonstrated Value → Offer → Decision

---

## 5. Follow-Up Cadence

Suggested early-stage cadence:

### Initial Contact

Send one concise discovery invitation.

### First Follow-Up

If there is no response, follow up after approximately three to five business days.

### Final Follow-Up

If there is still no response, send one final low-pressure message after approximately one week.

### Close

If no response follows, mark the lead `closed`.

Do not repeatedly contact an unresponsive prospect.

A future platform follow-up feature should be considered only after real lead volume makes manual tracking unreliable.

---

## 6. Commercial Evidence

For each product, track:

### Acquisition

- Prospects identified
- Outreach messages sent
- Responses received
- Discovery conversations completed

### Validation

- Prospects reporting the problem
- Prospects reporting meaningful consequences
- Prospects using inadequate workarounds
- Demonstrations completed
- Pilot invitations accepted

### Pilot

- Tenants provisioned
- Pilots started
- Real data entered
- Core workflows completed
- Pilots completed
- Participants requesting continued access

### Commercial

- Pricing conversations
- Willingness-to-pay signals
- Offers made
- Paid conversions
- Closed opportunities
- Reasons for loss

Do not optimize conversion percentages before enough real activity exists to make them meaningful.

---

## 7. Weekly Commercialization Review

Review the platform pipeline once each week.

For each product, ask:

1. How many leads are new?
2. Which leads were contacted?
3. Which discovery conversations occurred?
4. What evidence changed the product hypothesis?
5. Which leads are truly qualified?
6. Which qualified leads have a defined pilot step?
7. Which tenants are active pilots?
8. What blockers require action?
9. What work appears premature?
10. What is the single next commercialization milestone?

The review must clearly distinguish:

- Technical progress
- Documentation progress
- Demonstration progress
- Customer evidence
- Pilot evidence
- Commercial evidence

---

## 8. RenewalDesk Current Position

Current roadmap position:

Build → Document → **Demonstrate / Customer Validation** → Package → Sell

Current evidence:

- Technical MVP is deployed
- SMTP reminder delivery is production-verified
- Customer validation plan is documented
- Interview 001 is planned
- No completed customer interview is recorded
- No pilot evidence is recorded
- Pricing is not validated

Current guardrail:

Do not package or actively sell RenewalDesk yet.

Allowed commercialization work:

- Prospect identification
- Discovery outreach
- Interviews
- Demonstrations
- Evidence recording
- Narrow pilot preparation

Premature work includes:

- Final pricing
- Multiple subscription tiers
- Broad advertising
- Large sales campaigns
- Unvalidated feature expansion
- Claims of proven customer value

---

## 9. Single Next Milestone

Complete one real RenewalDesk customer discovery interview and demonstration, then record the evidence without identifying the prospect publicly.

Completion criteria:

- The prospect’s current workflow is recorded
- Problem severity is recorded
- Existing alternatives are recorded
- RenewalDesk is demonstrated
- Positive and negative feedback are recorded
- Pilot interest is recorded
- Willingness-to-pay evidence is recorded
- Assumptions are separated from facts
- The lead’s platform status reflects the evidence
