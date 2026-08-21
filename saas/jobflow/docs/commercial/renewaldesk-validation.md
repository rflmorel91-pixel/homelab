# RenewalDesk Customer Validation Plan

Version: 1.0
Status: Customer validation pending
Last updated: 2026-08-21

---

## 1. Product Hypothesis

RenewalDesk is a SaaS product for small organizations that need a reliable way to track recurring renewals, deadlines, owners, and reminder delivery.

The product hypothesis is that important renewals are currently managed through fragmented tools such as:

- Spreadsheets
- Calendar entries
- Email reminders
- Personal notes
- Vendor portals
- Informal staff knowledge

This fragmentation may cause missed deadlines, late fees, service interruptions, rushed decisions, and unclear ownership.

These assumptions have not yet been validated through completed customer interviews.

---

## 2. Current MVP

RenewalDesk currently supports:

- Tenant-scoped renewal records
- Renewal name and description
- Category and vendor tracking
- Renewal dates
- Cost tracking
- Status management
- Renewal ownership
- Owner email addresses
- Configurable reminder lead times
- Renewal urgency calculations
- Dashboard summaries
- Search and filtering
- Renewal record editing
- Persistent reminder queueing
- Idempotent reminder processing
- Sent and failed delivery tracking
- SMTP reminder delivery through Resend

The complete workflow has been production-tested with a real reminder email.

Technical completion does not constitute customer validation.

---

## 3. Target Customer Hypothesis

Initial prospects should be small organizations where one person manages several recurring obligations without dedicated procurement or compliance software.

Potential customer groups include:

- Small businesses
- Property managers
- Independent professional offices
- Nonprofit organizations
- Small IT service providers
- Consultants managing client renewals

Potential renewal types include:

- Software subscriptions
- Insurance policies
- Business licenses
- Professional certifications
- Service contracts
- Equipment warranties
- Domain names
- Vendor agreements

Customer interviews must determine which segment experiences the strongest and most urgent problem.

---

## 4. Validation Questions

### Current Process

- What recurring renewals or expiration dates do you manage?
- How do you track them today?
- Who is responsible for keeping the information current?
- How are reminders currently delivered?
- What happens when the responsible person is unavailable?

### Problem Severity

- Have you missed or nearly missed a renewal?
- What happened as a result?
- How often do renewal deadlines create urgent work?
- Which renewals carry the greatest operational or financial risk?
- How much time is spent checking spreadsheets, calendars, email, or vendor portals?

### Existing Alternatives

- What tools do you currently use?
- What works well about the current process?
- What is unreliable or frustrating?
- Have you tried a dedicated renewal-management product?
- Why have you continued using the current process?

### Product Evaluation

After discussing the existing workflow, demonstrate RenewalDesk and ask:

- Which part of this workflow would be useful?
- Which part would not fit the way you work?
- What critical information is missing?
- Who would enter and maintain the records?
- Would automated email reminders reduce a real risk?
- Would you be willing to test RenewalDesk with actual renewals?

### Commercial Signals

- What would need to be true for you to pay for this?
- Would you expect to pay monthly, annually, or per user?
- What existing cost or risk would justify the purchase?
- Who would approve the purchase?
- Would you participate in a short pilot?

Pricing answers are evidence, not commitments.

---

## 5. Demonstration Flow

Keep the demonstration under ten minutes.

1. Explain the problem hypothesis without claiming it is proven.
2. Show the renewal dashboard and urgency indicators.
3. Create one renewal record using a realistic example.
4. Assign an owner and owner email address.
5. Configure the reminder lead time.
6. Show search and filtering.
7. Edit the renewal record.
8. Explain reminder queueing and delivery history.
9. Show evidence of a successfully delivered reminder.
10. Return to discovery questions and ask for candid criticism.

The demonstration should support the interview, not replace it.

---

## 6. Evidence Record

For each conversation, record:

- Interview date
- Prospect and organization type
- Organization size
- Interviewee role
- Number and types of renewals managed
- Current tracking method
- Frequency of missed or nearly missed renewals
- Consequences of failure
- Strongest reported pain
- Existing alternatives
- Reaction to the demonstration
- Requested capabilities
- Pilot interest
- Willingness-to-pay signal
- Direct quotations or supporting details
- Follow-up action

Separate observed evidence from assumptions and interpretations.

---

## 7. Validation Threshold

Do not expand the product based on one unverified request.

Before packaging or selling RenewalDesk, seek:

- At least five customer discovery conversations
- At least three prospects reporting a recurring renewal problem
- At least two prospects identifying meaningful consequences or measurable effort
- At least two prospects willing to evaluate the product
- At least one prospect willing to use real renewal data in a pilot
- Direct feedback about willingness to pay

These are decision guidelines, not proof of product-market fit.

---

## 8. Premature Work Guardrail

Until customer evidence supports further development, avoid:

- Mobile applications
- Complex reporting
- Broad third-party integrations
- Multiple pricing tiers
- Enterprise procurement features
- Advanced role systems
- Custom notification channels
- Large UI redesigns
- Features requested by hypothetical customers

Allow additional engineering only when required to:

- Fix a demonstrated defect
- Protect security or data integrity
- Make the existing MVP demonstrable
- Support an agreed customer pilot
- Address a repeated, documented customer need

---

## 9. Roadmap Position

Current position:

Build → **Document** → Demonstrate → Customer Validation → Package → Sell

Build is complete enough for validation.

This document completes the initial documentation step. The project should now move to demonstration and customer conversations rather than additional speculative development.

---

## 10. Single Next Milestone

Complete one RenewalDesk customer discovery interview that includes a short product demonstration, and record the evidence in the repository.

Completion criteria:

- A real prospect participates
- Their current renewal workflow is documented
- Problem severity and consequences are recorded
- RenewalDesk is demonstrated
- Product reaction and pilot interest are recorded
- Assumptions are clearly separated from evidence
