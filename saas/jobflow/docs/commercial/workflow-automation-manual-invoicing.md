# Workflow Automation Manual Stripe Invoicing Procedure

Version: 1.0  
Status: Initial operating procedure  
Last updated: 2026-08-26  
Owner: FieldLookers LLC

---

## 1. Purpose

This procedure governs manual invoicing for fixed-price Workflow Automation Package engagements.

It covers:

- Stripe customer creation
- Deposit invoice creation
- Deposit payment confirmation
- Final invoice authorization and creation
- Payment evidence
- Unpaid invoices
- Corrections, refunds, cancellations, and disputes
- Engagement billing records

This procedure supplements `platform-pilot-billing.md`. If the documents conflict, stop and resolve the conflict before issuing an invoice.

---

## 2. Operating Model

During the manual phase:

- Stripe Invoicing and its hosted invoice page are used.
- The operator works through the Stripe Dashboard.
- Stripe is the billing and payment source of truth.
- The engagement record stores only the minimum billing references and status evidence.
- Customers enter payment information only on Stripe-hosted pages.
- No platform automation changes engagement state based on payment.

This procedure does not authorize:

- Stripe API integration
- Automated subscriptions
- Automatic payment collection
- Automatic engagement activation
- Product-specific payment code
- Storage of card or bank credentials
- Informal payment collection outside approved channels

---

## 3. Required Commercial Basis

Do not create a live invoice until all applicable items are confirmed:

- [ ] Qualified opportunity
- [ ] Customer legal or business name
- [ ] Authorized purchasing contact
- [ ] Billing contact and billing email
- [ ] Final Statement of Work
- [ ] Written SOW approval
- [ ] Total fixed price
- [ ] Deposit amount
- [ ] Final-payment amount
- [ ] Deposit plus final payment equals the total price
- [ ] Currency
- [ ] Invoice due dates
- [ ] Tax treatment reviewed
- [ ] Refund and cancellation terms completed
- [ ] Acceptance approver identified
- [ ] Engagement reference assigned
- [ ] Stripe live account ready to receive and pay out funds

Do not invoice from a draft SOW or unresolved payment placeholders.

---

## 4. Default Payment Structure

Unless an approved SOW states otherwise:

| Milestone | Amount | Trigger |
|---|---:|---|
| Deposit | 50% of fixed price | Approved SOW; before delivery begins |
| Final payment | 50% of fixed price | Written acceptance |

Example for a `$1,200.00 USD` engagement:

| Payment | Amount |
|---|---:|
| Deposit | `$600.00 USD` |
| Final payment | `$600.00 USD` |
| Total | `$1,200.00 USD` |

Verify the arithmetic independently before sending either invoice.

A different payment structure requires written commercial approval and must appear in the SOW.

---

## 5. Private Engagement Billing Record

Create or update a private engagement billing record before invoicing.

Record:

- Engagement reference
- Anonymized public reference, if needed
- Customer business name
- Billing contact
- Billing email
- SOW approval date
- Currency
- Total fixed price
- Deposit amount
- Final-payment amount
- Deposit invoice date
- Deposit invoice reference
- Deposit status
- Deposit payment date
- Delivery authorization date
- Written acceptance date
- Final invoice date
- Final invoice reference
- Final invoice status
- Final payment date
- Refund or cancellation status
- Dispute status
- Operator
- Notes excluding sensitive payment data

The record must not contain:

- Raw card numbers
- Card security codes
- Bank credentials
- Authentication data
- Stripe secret keys
- Payment-method details
- Hosted invoice URLs in public records
- Unnecessary customer personal information

Do not commit the private billing record to a public repository.

---

## 6. Stripe Customer Creation

Search Stripe before creating a customer.

Match using:

- Business or legal name
- Billing email
- Existing engagement references
- Other non-sensitive business information

Do not create a duplicate solely because capitalization or contact formatting differs.

If no correct customer exists, create one with only necessary information:

- Customer business or legal name
- Billing contact name
- Billing email
- Billing address when required
- Support or phone information only when operationally necessary
- Internal engagement reference in non-sensitive metadata

Before proceeding, confirm:

- [ ] Correct customer selected
- [ ] Billing email verified through the established customer channel
- [ ] Business name matches the approved SOW
- [ ] No duplicate customer record exists
- [ ] Metadata contains no secrets or sensitive project information

---

## 7. Deposit Invoice Creation

Create a one-time Stripe invoice.

### Recommended description

`Workflow Automation Package — 50% Project Deposit`

### Recommended line item

`50% deposit for the fixed-scope workflow automation engagement defined in [SOW REFERENCE]`

### Required invoice information

- Customer
- Engagement or SOW reference
- Deposit amount
- Currency
- Quantity `1`
- Due date matching the SOW
- Support contact
- Hosted invoice page enabled
- Correct tax treatment

### Recommended memo

Include:

- Deposit is required before delivery begins
- Engagement reference
- Remaining balance after the deposit
- Final balance becomes invoiceable after written acceptance
- Support contact

Do not include:

- Credentials
- Confidential workflow details
- Raw internal database identifiers
- Customer datasets
- Authentication information
- Unresolved legal or payment terms

---

## 8. Deposit Invoice Review

Before finalizing or sending:

- [ ] Correct Stripe customer selected
- [ ] Approved SOW exists
- [ ] Engagement reference is correct
- [ ] Description identifies a project deposit
- [ ] Amount equals the approved deposit
- [ ] Deposit and final amount equal the total price
- [ ] Currency is correct
- [ ] Due date matches the SOW
- [ ] Invoice is one-time
- [ ] Recurring billing is disabled
- [ ] Tax treatment is correct
- [ ] Billing email is correct
- [ ] Hosted invoice page is enabled
- [ ] Support details are correct
- [ ] Invoice contains no sensitive information
- [ ] Draft preview has been reviewed

Use a second review for the first live professional-services invoice or any unusual amount or tax treatment.

---

## 9. Deposit Invoice Delivery

Finalize and send the invoice through Stripe.

The customer should receive:

- Stripe invoice email
- Hosted invoice link
- Deposit amount
- Description
- Due date
- Downloadable invoice
- Stripe payment confirmation after payment

If needed, send the hosted invoice link through the verified business communication channel.

Never request card or bank information through:

- Email
- Text message
- Chat
- Phone notes
- GitHub
- Source control
- Engagement notes
- Platform lead notes

The customer must enter payment information only on Stripe-hosted pages.

Record the invoice reference and sent date in the private engagement billing record.

---

## 10. Deposit Payment Confirmation

Do not begin delivery merely because the customer states that payment was sent.

Verify directly in Stripe:

- [ ] Invoice status is `paid`
- [ ] Amount paid equals the deposit invoice
- [ ] Currency is correct
- [ ] Customer matches the engagement
- [ ] Invoice reference matches the billing record
- [ ] Payment is not pending
- [ ] Payment is not failed, refunded, or disputed
- [ ] Stripe shows no unresolved condition preventing reliance on payment

Stripe’s displayed payment status is the source of truth during the manual phase.

After confirmation:

1. Record the paid status.
2. Record the payment date.
3. Record the Stripe invoice reference.
4. Record the operator.
5. Record delivery authorization.
6. Notify the workflow owner that delivery may begin.

Do not record raw payment-method information.

---

## 11. Delivery Start Gate

Delivery may begin only when:

- The SOW is approved.
- The deposit invoice is paid in Stripe.
- Required access and data controls are complete.
- Customer dependencies required for the start are ready.
- The delivery owner records authorization to proceed.

An unpaid, pending, failed, void, or disputed deposit does not authorize delivery.

An exception requires written commercial approval and a documented risk decision.

---

## 12. Final Invoice Authorization

The final invoice is authorized only after written acceptance under the SOW.

Acceptable evidence identifies:

- Engagement
- Deliverables reviewed
- Acceptance decision
- Authorized acceptance approver
- Date

Do not treat the following alone as written acceptance:

- Verbal praise
- Demonstration attendance
- System access
- Informal usage
- Silence
- A request for new work
- Payment promises

If the customer reports unmet acceptance criteria, follow the SOW acceptance procedure before invoicing the final balance.

New features or changed requirements follow change control and do not reduce the approved fixed price unless both parties approve a commercial change in writing.

---

## 13. Final Invoice Creation

Create a separate one-time Stripe invoice.

### Recommended description

`Workflow Automation Package — Final Project Payment`

### Recommended line item

`Final 50% payment following written acceptance of the engagement defined in [SOW REFERENCE]`

### Required invoice information

- Correct Stripe customer
- Engagement or SOW reference
- Final-payment amount
- Currency
- Quantity `1`
- Due date matching the SOW
- Support contact
- Hosted invoice page enabled
- Correct tax treatment

### Recommended memo

Include:

- Written acceptance date
- Engagement reference
- This invoice represents the remaining approved project balance
- Support contact

Do not combine unrelated engagements or out-of-scope work into the final invoice.

Approved change-order charges must use clearly identified line items or a separate invoice consistent with the written change order.

---

## 14. Final Invoice Review and Delivery

Before sending:

- [ ] Written acceptance evidence exists
- [ ] Acceptance came from the authorized approver
- [ ] Correct customer selected
- [ ] Engagement reference is correct
- [ ] Final amount matches the SOW
- [ ] Deposit and final amounts reconcile to the total
- [ ] Approved change orders are separately identifiable
- [ ] Currency is correct
- [ ] Due date matches the SOW
- [ ] Invoice is one-time
- [ ] Recurring billing is disabled
- [ ] Tax treatment is correct
- [ ] Billing email is correct
- [ ] Hosted invoice page is enabled
- [ ] No sensitive information appears
- [ ] Draft preview has been reviewed

Finalize and send through Stripe.

Record:

- Written acceptance date and reference
- Final invoice reference
- Invoice sent date
- Amount
- Due date
- Operator

---

## 15. Final Payment Confirmation

Verify directly in Stripe:

- [ ] Final invoice status is `paid`
- [ ] Amount paid matches the invoice
- [ ] Currency is correct
- [ ] Customer and engagement match
- [ ] Payment is not pending
- [ ] Payment is not failed, refunded, or disputed

Then record:

- Final payment date
- Final paid status
- Invoice reference
- Operator
- Remaining balance of zero, when applicable

A sent or viewed invoice is not payment confirmation.

---

## 16. Payment Evidence

Payment evidence associated with the engagement should contain:

- Engagement reference
- Stripe customer reference
- Stripe invoice reference
- Invoice type: deposit, final, or change order
- Invoice amount and currency
- Invoice sent date
- Stripe status
- Payment-confirmed date
- Operator
- Refund or dispute status, if applicable

Prefer provider references and status records over screenshots.

If a screenshot is operationally necessary:

1. Capture only the required area.
2. Remove payment-method and personal information.
3. Review browser tabs, notifications, filenames, and addresses.
4. Store it only in the approved private engagement location.
5. Do not place it in a public GitHub issue.

Customer screenshots and email notices do not replace verification in Stripe.

---

## 17. Unpaid or Failed Deposit Invoice

If the deposit invoice is unpaid or failed:

1. Do not begin delivery.
2. Verify the billing email.
3. Review the Stripe status.
4. Allow configured Stripe reminders.
5. Send one direct professional follow-up when appropriate.
6. Ask whether the customer intends to proceed.
7. Correct a verified invoice error before requesting payment.
8. Void the invoice if the engagement is declined or cancelled.
9. Record the outcome privately.
10. Update the commercial opportunity appropriately.

Do not repeatedly pressure the customer.

Do not mark the engagement paid based on a promise, screenshot, or pending bank payment.

---

## 18. Unpaid or Failed Final Invoice

If the final invoice is unpaid:

1. Confirm it was sent to the correct billing contact.
2. Confirm the amount and due date match the SOW.
3. Review Stripe’s current status.
4. Allow configured reminders.
5. Send a direct business follow-up when appropriate.
6. Preserve the written acceptance and delivery evidence.
7. Follow only the approved late-payment or collection terms.
8. Do not invent fees or penalties not contained in reviewed terms.
9. Record the current status privately.
10. Escalate material collection questions for qualified legal or accounting guidance.

Do not revoke or damage delivered customer assets unless expressly authorized by reviewed contractual terms and applicable law.

---

## 19. Invoice Corrections

If an unsent draft is incorrect, correct it and repeat the review.

If a finalized or sent invoice is incorrect:

1. Stop requesting payment on the incorrect amount.
2. Review Stripe’s supported correction, void, or credit-note workflow.
3. Preserve the original provider record.
4. Correct the customer, amount, tax, or description through Stripe.
5. Send the corrected document through Stripe.
6. Update the private engagement billing record.
7. Notify the customer clearly without exposing sensitive information.

Never conceal an invoice correction by altering only the local engagement record.

---

## 20. Refunds

Refund eligibility must follow the approved SOW, governing agreement, applicable law, and qualified guidance.

Do not issue a refund solely from an informal request without verifying:

- Customer identity
- Engagement
- Original invoice
- Original payment
- Requesting person’s authority
- Approved refund basis
- Amount
- Commercial approval

Process approved refunds through Stripe to the original payment method.

Do not refund through cash, peer-to-peer applications, or a different payment destination unless required and safely verified under approved guidance.

Record:

- Engagement reference
- Invoice reference
- Refund amount
- Reason category
- Approver
- Stripe refund status
- Refund date
- Customer notification date
- Operator

Do not record unnecessary payment-method details.

---

## 21. Cancellation Handling

### Before deposit payment

- Do not begin delivery.
- Void or close the unpaid invoice when appropriate.
- Record that the engagement did not start.
- Update the commercial opportunity.

### After deposit payment but before delivery

- Stop work.
- Review the approved cancellation and refund terms.
- Determine completed preparation costs or obligations only under those terms.
- Obtain commercial approval.
- Process any approved refund through Stripe.
- Record the outcome.

### After delivery begins

- Stop new work at the approved boundary.
- Secure customer systems and data.
- Record completed and incomplete deliverables.
- Review payment, refund, ownership, and handoff terms.
- Complete an access and data disposition.
- Issue only invoices or credits authorized by the approved terms.
- Obtain qualified guidance for unresolved disputes.

### After written acceptance

- Preserve acceptance evidence.
- Follow the approved final-payment, refund, and cancellation terms.
- Do not treat cancellation as automatically eliminating an accepted payment obligation.

Do not promise a refund outcome before reviewing the governing terms and facts.

---

## 22. Disputes and Chargebacks

If a payment is disputed:

1. Stop new commercial activity when appropriate.
2. Review the invoice, SOW, acceptance evidence, and communications.
3. Preserve relevant records.
4. Respond through Stripe’s dispute process.
5. Disclose only necessary evidence.
6. Do not expose credentials or unrelated customer data.
7. Do not contact the customer aggressively.
8. Record the outcome privately.
9. Obtain qualified guidance when needed.

Do not create automated dispute handling during the manual phase.

---

## 23. Security and Separation of Duties

The operator must never:

- Store raw payment-card data
- Store card security codes
- Store bank credentials
- Ask a customer to send payment credentials
- Commit Stripe keys
- Log payment secrets
- Copy payment authentication data into the platform
- Treat customer input as verified payment status
- Use public issues for billing records
- Mix unrelated customer invoices
- Create recurring billing without authorization

For the first live service engagement, use a second-person or deliberate independent review before sending each invoice.

---

## 24. Reconciliation Checklist

At engagement completion:

- [ ] Total fixed price matches the SOW
- [ ] Deposit amount matches the SOW
- [ ] Final amount matches the SOW
- [ ] Approved change orders are accounted for
- [ ] Credits and refunds are accounted for
- [ ] Stripe invoice references are recorded
- [ ] Stripe statuses are verified
- [ ] Payment dates are recorded
- [ ] Remaining balance is recorded
- [ ] Disputes are recorded
- [ ] Billing record contains no sensitive payment data
- [ ] Commercial outcome is updated
- [ ] Required accounting or tax records are retained appropriately

The engagement is not financially reconciled merely because delivery is complete.

---

## 25. Deposit Invoice Checklist

- [ ] Qualified opportunity
- [ ] Approved SOW
- [ ] Correct Stripe customer
- [ ] Billing contact verified
- [ ] Deposit arithmetic verified
- [ ] Invoice description correct
- [ ] Engagement reference included
- [ ] Currency and due date correct
- [ ] Tax treatment reviewed
- [ ] One-time invoice confirmed
- [ ] Hosted invoice page enabled
- [ ] No sensitive information included
- [ ] Draft preview reviewed
- [ ] Invoice sent through Stripe
- [ ] Invoice reference recorded
- [ ] Stripe shows `paid` before delivery begins

---

## 26. Final Invoice Checklist

- [ ] Written acceptance received
- [ ] Acceptance approver verified
- [ ] Correct Stripe customer
- [ ] Final-payment arithmetic verified
- [ ] Deposit and final amounts reconcile
- [ ] Change orders separately identified
- [ ] Currency and due date correct
- [ ] Tax treatment reviewed
- [ ] One-time invoice confirmed
- [ ] Hosted invoice page enabled
- [ ] No sensitive information included
- [ ] Draft preview reviewed
- [ ] Invoice sent through Stripe
- [ ] Invoice reference recorded
- [ ] Stripe payment status confirmed
- [ ] Remaining balance recorded

---

## 27. Completion Evidence

Record without payment credentials or unnecessary customer information:

- Engagement reference:
- SOW approval date:
- Total fixed price:
- Deposit invoice reference:
- Deposit amount:
- Deposit sent date:
- Deposit paid date:
- Delivery authorization date:
- Written acceptance reference:
- Written acceptance date:
- Final invoice reference:
- Final amount:
- Final invoice sent date:
- Final invoice paid date:
- Change-order invoice references:
- Refund or credit references:
- Dispute status:
- Remaining balance:
- Reconciliation date:
- Operator:
- Unresolved actions:
