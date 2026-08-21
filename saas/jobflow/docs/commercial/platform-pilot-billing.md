# Platform Pilot Billing and Payment Procedure

Version: 1.0
Status: Initial operating procedure
Last updated: 2026-08-21
Owner: SaaS Platform

---

## 1. Purpose

This document defines the shared pilot billing and payment process for every SaaS product registered on the platform.

It applies to:

- RenewalDesk
- JobFlow
- Future platform products
- Products developed by external developers under the platform contract

The platform owns the billing process.

Individual products remain responsible for their product-specific value proposition, pilot workflow, success criteria, and validated pricing.

---

## 2. Architectural Boundary

### Platform Responsibilities

The platform owns:

- Commercial leads
- Lead qualification
- Pilot eligibility
- Pilot agreements
- Billing policy
- Payment-provider relationship
- Payment confirmation
- Tenant provisioning authorization
- Tenant lifecycle
- Platform audit records
- Future subscriptions
- Future billing administration

### Product Responsibilities

Each product owns:

- Product workflow
- Product-specific data
- Product demonstration
- Pilot success criteria
- Product usage evidence
- Product-specific support requirements
- Validated pricing evidence

### Payment Provider Responsibilities

Stripe will initially own:

- Customer billing profiles
- Hosted invoices
- Hosted payment pages
- Payment-method collection
- Card and bank-payment details
- Payment authentication
- Payment receipts
- Payment status
- Refund processing
- Payment reconciliation

The SaaS platform must never collect or store raw card numbers, bank credentials, security codes, or payment authentication data.

### JobFlow Boundary

JobFlow invoices and payments represent transactions between a JobFlow tenant and that tenant’s customers.

They must never be used to bill a customer for:

- Platform access
- RenewalDesk
- JobFlow subscriptions
- Pilots
- Any other SaaS product

Platform billing and JobFlow operational billing are separate systems.

---

## 3. Commercial Roadmap

Platform billing follows:

Build → Document → Demonstrate → Customer Validation → Package → Sell

Billing capabilities must not move ahead of customer evidence.

Current operating phase:

- Manual platform billing procedure
- Stripe-hosted invoicing
- No custom checkout
- No subscription database
- No automatic tenant suspension for nonpayment
- No pricing tiers
- No usage-based billing

Future automation requires demonstrated commercial demand.

---

## 4. Pilot Types

The platform supports two early-stage pilot types.

### Validation Pilot

Purpose:

- Validate a product problem
- Observe real use
- Test the product workflow
- Collect product and customer evidence

Default terms:

- No charge
- 30-day duration
- One initial validation pilot per product
- Narrow success criteria
- Real customer participation
- Scheduled review at the end
- No commitment to custom development
- No automatic extension

A free validation pilot requires the participant to provide:

- Realistic or real operating data
- Honest workflow feedback
- At least one pilot review conversation
- Permission to record anonymized findings
- A decision about continued use

A free account without agreed learning goals is not a validation pilot.

### Paid Pilot

Purpose:

- Test willingness to pay
- Validate the purchasing process
- Measure support and onboarding effort
- Test commercial value
- Prepare for a recurring offer

Default hypothesis:

- One-time price: $99 USD
- Duration: 30 days
- Payment due before provisioning
- No automatic renewal
- No subscription commitment
- One product per pilot
- One tenant per pilot
- Standard onboarding included
- Custom development excluded

The $99 amount is a pricing hypothesis, not a validated or permanent platform price.

A product may use a different pilot price only when documented evidence supports the change.

---

## 5. Pilot Eligibility

A lead is eligible for a validation pilot when:

- The lead is associated with the correct product
- A discovery conversation occurred
- A meaningful problem was identified
- The product is relevant to the problem
- The prospect agrees to use the product
- A pilot owner is identified
- Pilot success criteria are defined
- A review date is agreed

A lead is eligible for a paid pilot when:

- The product has completed its initial validation pilot
- The product showed useful or promising value
- The prospect understands the pilot scope
- The prospect agrees to the price
- A purchase decision-maker is identified
- Billing information is available
- A pilot owner is identified
- Success criteria are defined

A positive reaction to a demonstration is not enough to authorize a pilot.

---

## 6. Product Billing Configuration

Every invoice must identify the product being purchased.

Before billing, record:

- Platform product ID
- Product name
- Lead ID
- Business or customer name
- Billing contact
- Billing email
- Pilot type
- Pilot price
- Currency
- Pilot start date
- Pilot end date
- Tenant owner
- Tenant slug
- Success criteria
- Operator responsible for provisioning

Do not store sensitive billing information in repository documents.

Public repository records must use anonymized customer identifiers.

---

## 7. Stripe Operating Decision

The initial payment provider is Stripe.

The initial Stripe capability is:

Stripe Invoicing with a Stripe-hosted invoice page.

Do not initially implement:

- Stripe API integration
- Stripe Checkout integration
- Subscription webhooks
- Customer portal integration
- Automatic entitlement changes
- Automatic tenant suspension
- Usage metering
- Multiple price objects
- Product-specific billing code

The operator creates and manages pilot invoices through the Stripe Dashboard.

This keeps payment handling outside the SaaS application while the commercial model remains unvalidated.

---

## 8. Stripe Account Preparation

Before issuing the first paid invoice:

1. Complete Stripe account verification.
2. Configure the legal business name.
3. Configure customer-facing support details.
4. Add platform branding.
5. Confirm the payout bank account.
6. Enable two-factor authentication.
7. Restrict administrative access.
8. Configure invoice numbering.
9. Configure invoice email settings.
10. Review enabled payment methods.
11. Confirm refund permissions.
12. Determine applicable tax obligations with qualified guidance.

Do not issue a live invoice until the Stripe account is ready to accept and pay out funds.

---

## 9. Paid Pilot Invoice Creation

For a qualified paid pilot, create a customer in Stripe.

Customer information should include only what is necessary:

- Business or customer name
- Billing contact
- Billing email
- Billing address when required
- Internal lead reference in non-sensitive metadata

Create a one-time invoice with:

### Invoice Description

`[Product Name] — 30-Day SaaS Pilot`

Example:

`RenewalDesk — 30-Day SaaS Pilot`

### Line Item

`30-day pilot access, standard onboarding, and pilot review`

### Amount

Default:

`$99.00 USD`

### Quantity

`1`

### Payment Terms

Default:

`Due upon receipt`

### Memo

Include:

- Pilot start after confirmed payment
- Pilot duration
- No automatic renewal
- Product name
- Support contact
- Pilot reference

Do not include:

- Passwords
- Authentication data
- Sensitive customer data
- Raw internal database identifiers
- Confidential interview details

---

## 10. Invoice Review

Before sending an invoice, verify:

- The correct customer is selected
- The correct product is named
- The amount matches the agreed pilot price
- The currency is correct
- The billing email is correct
- The pilot duration is stated
- The invoice is one-time
- Automatic recurring billing is disabled
- Tax treatment is correct
- The hosted payment page is enabled
- Support contact information is correct
- No sensitive information appears

A second review should be used for the first live paid pilot.

---

## 11. Invoice Delivery

Send the invoice through Stripe.

The customer should receive:

- Stripe invoice email
- Hosted invoice link
- Invoice amount
- Product description
- Payment due date
- Downloadable invoice
- Payment confirmation after payment

If necessary, the operator may copy the hosted invoice link and send it through an established customer communication channel.

Never request card or bank information through:

- Email
- Text message
- Chat
- Phone notes
- Repository files
- Platform lead notes

The customer must enter payment information only on Stripe-hosted pages.

---

## 12. Payment Methods

Initial supported methods:

- Card
- ACH or bank payment when available through Stripe

Do not initially accept:

- Cryptocurrency
- Cash
- Peer-to-peer personal payment applications
- Stored card details outside Stripe
- Manual bank credentials
- Split payments
- Installment plans

Check may be accepted only when there is a documented business reason and a reconciliation procedure.

---

## 13. Payment Confirmation

A paid pilot may be provisioned only after Stripe shows the invoice as paid.

Before provisioning, verify:

- Invoice status is `paid`
- Amount paid matches the invoice
- Customer matches the lead
- Product matches the intended tenant
- Payment is not disputed or failed
- Pilot dates are confirmed
- Tenant owner is confirmed

Do not rely only on:

- Customer screenshots
- Customer statements
- Email notifications
- Pending bank-payment status

Stripe’s payment status is the payment source of truth during the manual phase.

---

## 14. Tenant Provisioning

After payment confirmation:

1. Open platform commercialization.
2. Confirm the lead is `qualified`.
3. Confirm the correct product.
4. Select the initial tenant owner.
5. Confirm the tenant slug.
6. Provision the tenant.
7. Confirm the lead becomes `converted`.
8. Confirm the tenant is active.
9. Confirm the owner can sign in.
10. Record the pilot start and end dates privately.
11. Send onboarding instructions.
12. Schedule the pilot review.

For a free validation pilot, the same provisioning process applies without an invoice.

Converted means provisioned.

Converted does not necessarily mean:

- Paid subscriber
- Commercially validated customer
- Recurring customer
- Successful pilot

---

## 15. Billing Recordkeeping

During the manual phase, Stripe is the billing and payment system of record.

The platform database does not yet store:

- Stripe customer IDs
- Stripe invoice IDs
- Payment intents
- Payment methods
- Card details
- Bank details
- Subscription records
- Refund records
- Dispute records

Maintain a private operator billing register containing:

- Anonymized customer reference
- Product
- Lead reference
- Pilot type
- Invoice date
- Invoice amount
- Payment status
- Payment date
- Pilot start
- Pilot end
- Refund status
- Operator notes

Do not commit customer billing data to the public repository.

Do not duplicate sensitive Stripe information in platform records.

---

## 16. Failed or Unpaid Invoices

If an invoice is unpaid:

1. Do not provision the tenant.
2. Confirm the billing email is correct.
3. Allow Stripe to send the configured reminder.
4. Send one direct business follow-up if necessary.
5. Ask whether the prospect still intends to proceed.
6. Void or close the invoice if the pilot is declined.
7. Update the lead according to the commercial outcome.

Do not repeatedly pressure the prospect.

An unpaid invoice is commercial evidence and should influence willingness-to-pay conclusions.

---

## 17. Refunds

Default pilot refund procedure:

### Before Provisioning

If payment was received but the tenant has not been provisioned:

- Issue a full refund when the customer withdraws.
- Cancel the pilot.
- Record the reason privately.

### After Provisioning

Review the circumstances.

Issue a full or partial refund when:

- The product was materially unavailable
- The promised pilot could not be delivered
- A platform defect prevented meaningful use
- The customer was billed incorrectly
- The wrong product or amount was invoiced

Do not promise that every completed pilot is nonrefundable without appropriate legal review and clear customer terms.

Process refunds through Stripe.

Do not refund outside the original payment channel unless required and safely verified.

---

## 18. Disputes and Chargebacks

If a payment is disputed:

1. Do not contact the customer aggressively.
2. Review the invoice and pilot agreement.
3. Preserve relevant business records.
4. Respond through Stripe’s dispute process.
5. Do not expose sensitive customer information.
6. Suspend new commercial activity when appropriate.
7. Record the outcome privately.
8. Review whether the invoice or onboarding process caused confusion.

Do not build automated dispute handling during the pilot phase.

---

## 19. Cancellation and Expiration

A pilot does not renew automatically.

Before the pilot end date:

1. Review product usage.
2. Conduct the pilot review.
3. Evaluate success criteria.
4. Discuss continued access.
5. Discuss willingness to pay.
6. Decide whether to extend, package, sell, or stop.

If the pilot ends without an agreement:

- Notify the tenant owner
- Preserve data according to the applicable policy
- Suspend or deactivate access through platform administration
- Do not delete customer data without an approved retention process
- Record the commercial outcome

---

## 20. Free-to-Paid Decision

Do not convert a free validation pilot into a paid relationship automatically.

A paid offer requires:

- Demonstrated customer value
- Completed pilot review
- Clear product scope
- Validated buyer or decision-maker
- Agreed price
- Agreed billing period
- Support expectations
- Cancellation terms
- Production readiness

If these are not present, continue validation or end the pilot.

---

## 21. Recurring Subscription Gate

Do not implement recurring subscription billing until:

- At least one product completes a real validation pilot
- At least two paid pilots are completed
- Customers demonstrate continuing value
- Customers request or accept recurring access
- A recurring price is tested
- Billing ownership is defined
- Access and cancellation behavior are defined
- Failed-payment behavior is defined
- Refund and dispute procedures are operational
- Tax obligations are understood
- Provider webhook security is designed
- Subscription tests can be automated

Only then should the platform add:

- Billing customers
- Product prices
- Subscriptions
- Billing periods
- Invoice references
- Payment-state synchronization
- Webhook processing
- Entitlement enforcement
- Customer billing portal
- Cancellation workflow
- Failed-payment recovery
- Platform billing administration

Recurring billing must remain a platform capability, not product-owned code.

---

## 22. Future Platform Billing Model

When the recurring-subscription gate is met, the likely platform entities are:

### Billing Customer

Links a tenant or commercial customer to the payment provider.

### Product Price

Defines a product-specific amount, currency, and billing interval.

### Subscription

Links:

- Billing customer
- Tenant
- Product
- Product price
- Provider subscription
- Subscription status
- Billing dates

### Billing Event

Records normalized provider events such as:

- Invoice created
- Invoice paid
- Payment failed
- Subscription activated
- Subscription canceled
- Refund issued
- Dispute opened

### Entitlement

Controls whether the tenant may use the product.

These are future architecture directions, not authorized implementation work.

---

## 23. Security Rules

The platform must never:

- Store raw payment-card data
- Store card security codes
- Store customer bank credentials
- Log payment secrets
- Commit Stripe keys
- Expose provider secrets to frontend code
- Trust unverified webhook payloads
- Provision from a client-side payment claim
- Accept payment status from user input
- Mix product invoices with platform billing

Future Stripe secrets must be stored through deployment secrets or protected environment configuration.

---

## 24. Audit Requirements

During the manual phase, retain evidence of:

- Pilot approval
- Agreed product
- Agreed amount
- Invoice sent
- Payment confirmed
- Tenant provisioned
- Pilot started
- Pilot ended
- Refund or dispute outcome
- Commercial decision

Do not place sensitive invoice or customer information in public audit output.

Future automated billing actions should create platform audit events.

---

## 25. Product-Agnostic Requirements

The billing procedure must work without product-specific code.

Every registered product should be able to supply:

- Product ID
- Product name
- Pilot description
- Pilot success criteria
- Pilot price hypothesis
- Future subscription price hypotheses

The platform supplies:

- Lead workflow
- Qualification
- Pilot authorization
- Invoice procedure
- Payment confirmation
- Provisioning
- Tenant lifecycle
- Audit
- Future subscription infrastructure

A product must not create its own Stripe integration.

---

## 26. Current Application

### RenewalDesk

Current stage:

Demonstration and customer validation.

Current billing decision:

- Discovery is free
- Demonstration is free
- Initial validation pilot will be free
- A later qualified paid pilot will test the $99 hypothesis
- No RenewalDesk subscription exists yet

### JobFlow

Current billing decision:

- JobFlow customer invoices remain product workflow records
- Platform access billing remains separate
- No JobFlow platform subscription exists yet
- Any future JobFlow pilot uses this shared procedure

### Future Products

Future products inherit this procedure automatically.

They may not bypass platform billing or independently collect payment credentials.

---

## 27. Operating Checklist

Before a free pilot:

- [ ] Discovery completed
- [ ] Lead qualified
- [ ] Product confirmed
- [ ] Pilot owner confirmed
- [ ] Success criteria recorded
- [ ] Pilot dates agreed
- [ ] Tenant provisioned
- [ ] Review scheduled

Before a paid pilot:

- [ ] Product completed initial validation pilot
- [ ] Discovery completed
- [ ] Lead qualified
- [ ] Product confirmed
- [ ] Price agreed
- [ ] Billing contact confirmed
- [ ] Stripe invoice reviewed
- [ ] Stripe invoice sent
- [ ] Stripe payment confirmed
- [ ] Tenant provisioned
- [ ] Pilot dates recorded
- [ ] Review scheduled

At pilot completion:

- [ ] Usage reviewed
- [ ] Success criteria reviewed
- [ ] Customer feedback recorded
- [ ] Willingness to pay reviewed
- [ ] Continuation decision made
- [ ] Tenant lifecycle decision made
- [ ] Commercial evidence updated

---

## 28. Roadmap Position

Current platform billing position:

**Document**

The procedure is defined, but paid-pilot demand has not been validated.

Do not proceed to custom billing implementation yet.

The next billing milestone is:

Use this procedure for the first real qualified pilot when customer evidence supports either a free validation pilot or a paid pilot.

The next overall product milestone remains:

Complete one real customer discovery interview and demonstration.
