# Workflow Automation Secure Handoff Record

Version: 1.0  
Status: Reusable engagement template  
Last updated: 2026-08-26  
Owner: FieldLookers LLC

Complete this record with:

- `workflow-automation-acceptance-template.md`
- `workflow-automation-credential-data-handling.md`
- The approved Statement of Work

Do not send this record with unresolved placeholders or secret values.

---

## 1. Engagement Identification

- Engagement reference: [REFERENCE]
- Statement of Work reference: [SOW REFERENCE]
- Customer or contracting partner: [LEGAL NAME]
- End client, if applicable: [NAME]
- Delivered workflow: [WORKFLOW]
- Written acceptance reference: [REFERENCE]
- Written acceptance date: [YYYY-MM-DD]
- Handoff date: [YYYY-MM-DD]
- FieldLookers delivery owner: [NAME]
- Customer operational owner: [NAME, TITLE, EMAIL]
- Customer credential owner: [NAME, TITLE, EMAIL]
- Customer incident contact: [NAME, METHOD]
- Correction-period contact, if applicable: [NAME, METHOD]

---

## 2. Delivered Workflow and Artifacts

Delivered workflow:

[SUMMARY]

| Artifact | Version | Delivery location | Customer owner | Verified |
|---|---|---|---|---|
| [ARTIFACT] | [VERSION] | [LOCATION] | [OWNER] | Yes/No |

Confirm:

- [ ] Operating documentation delivered
- [ ] Configuration or deployment notes delivered
- [ ] Source or executable artifacts delivered when included
- [ ] Artifact ownership or license treatment matches the SOW
- [ ] Third-party dependencies and licenses identified
- [ ] Customer can access every required deliverable
- [ ] Delivered materials contain no credentials

---

## 3. Deployment and Configuration Notes

- Environment: [TEST / PRODUCTION / OTHER]
- Deployment location: [LOCATION]
- Deployment date: [YYYY-MM-DD]
- Deployed version: [VERSION]
- Deployment owner: [OWNER]
- Customer system owner: [OWNER]
- Configuration location: [LOCATION]
- Runtime dependencies: [DEPENDENCIES]
- External services: [SERVICES]
- Scheduled processes: [SCHEDULES]
- Monitoring included: [YES / NO / DETAILS]
- Backup included: [YES / NO / DETAILS]
- Customer-operated steps: [STEPS]

Do not reproduce credentials, tokens, private keys, connection strings, or recovery codes.

---

## 4. Operating Procedure

### Normal operation

1. [STEP]
2. [STEP]
3. [STEP]

### Human review

- Review trigger: [TRIGGER]
- Reviewer: [ROLE]
- Review action: [ACTION]
- Escalation condition: [CONDITION]
- Escalation contact: [CONTACT]

### Expected outputs

[OUTPUTS]

### Failure indicators

[INDICATORS]

### Safe-stop procedure

[SAFE-STOP STEPS]

---

## 5. Recovery or Rollback Instructions

- Recovery owner: [OWNER]
- Backup or recovery source: [LOCATION OR NOT INCLUDED]
- Last verified recovery date: [DATE OR NOT VERIFIED]
- Rollback trigger: [TRIGGER]
- Maximum safe rollback window: [WINDOW]
- Data-loss implications: [IMPLICATIONS]
- Vendor dependency: [DEPENDENCY]
- Required authorization: [AUTHORIZER]

Rollback steps:

1. [STEP]
2. [STEP]
3. [STEP]

Verification after recovery or rollback:

1. [CHECK]
2. [CHECK]
3. [CHECK]

If rollback or recovery is not included, state that explicitly and identify the customer’s responsibility.

---

## 6. Known Limitations

| Limitation | Operational impact | Workaround or required action | Owner |
|---|---|---|---|
| [LIMITATION] | [IMPACT] | [ACTION] | [OWNER] |

- Remaining manual steps: [STEPS]
- Unsupported conditions: [CONDITIONS]
- Volume or usage boundary: [BOUNDARY]
- Vendor limitations: [LIMITATIONS]
- Open security actions: [NONE OR ACTIONS]

Confirm:

- [ ] Limitations match the acceptance record
- [ ] No failed acceptance criterion is concealed as a limitation
- [ ] Customer operational owner acknowledges the limitations

---

## 7. Credential and Access Disposition

Do not record secret values.

| System or account | Environment | Owner | Handoff outcome | Completed by | Date | Verification |
|---|---|---|---|---|---|---|
| [ITEM] | Test/Production | [OWNER] | Revoked/Transferred/Retained/Expiring | [PERSON] | [DATE] | [REFERENCE] |

Confirm:

- [ ] Every account has a recorded owner
- [ ] FieldLookers named accounts are revoked or separately authorized
- [ ] Shared credentials are rotated by the system owner
- [ ] Temporary credentials and tokens are revoked
- [ ] Secure shares are expired or revoked
- [ ] Production access is removed unless separately authorized
- [ ] Multi-factor authentication ownership is confirmed
- [ ] Recovery-code ownership is confirmed
- [ ] Continued support access is governed by a separate written agreement

Handoff is incomplete while any access item lacks a disposition.

---

## 8. Data Disposition

| Data category or copy | Owner | Location | Outcome | Completion date | Verification |
|---|---|---|---|---|---|
| [ITEM] | [OWNER] | [LOCATION] | Returned/Deleted/Retained/Customer-controlled | [DATE] | [REFERENCE] |

Confirm:

- [ ] Working data disposition recorded
- [ ] Test data disposition recorded
- [ ] Production-data copies reviewed
- [ ] Local and temporary storage reviewed
- [ ] Logs and screenshots reviewed
- [ ] Backup and archive implications recorded
- [ ] Retained data has a purpose and deletion deadline
- [ ] Deletion evidence contains no copied customer data
- [ ] Customer confirms the disposition

---

## 9. Security and Incident Transition

- Customer primary incident contact: [CONTACT]
- Customer backup incident contact: [CONTACT]
- FieldLookers correction-period contact: [CONTACT OR NOT APPLICABLE]
- Approved urgent channel: [CHANNEL]
- Vendor escalation contact: [CONTACT OR NOT APPLICABLE]
- Open incident: [NONE OR REFERENCE]
- Open security action: [NONE OR ACTION]
- Responsibility transition date and time: [DATE/TIME/TIMEZONE]

Confirm:

- [ ] Customer understands the incident path
- [ ] Open incidents or security actions are disclosed
- [ ] FieldLookers incident responsibility after handoff matches the support boundary
- [ ] No public issue contains incident or credential information

---

## 10. Support Boundary

Included correction period:

[PERIOD OR NOT INCLUDED]

Correction-period start:

[DATE]

Correction-period end:

[DATE]

Included correction work:

[DEFINED FAILURE-TO-MEET-CRITERIA WORK]

Not included:

- New features
- Changed requirements
- New data conditions
- Third-party or vendor changes
- Hosting, monitoring, maintenance, or incident response unless expressly included
- Misuse outside documented operating boundaries
- Out-of-scope integrations or support

Ongoing support arrangement:

[NOT INCLUDED OR SEPARATE AGREEMENT REFERENCE]

Support contact procedure:

[PROCEDURE]

Requests outside this boundary require a separate quote, change order, or support agreement.

---

## 11. Commercial Completion

- Written acceptance recorded: Yes / No
- Final invoice authorized: Yes / No
- Final invoice reference: [REFERENCE OR PENDING]
- Final invoice amount: $[AMOUNT]
- Final invoice status: [DRAFT / SENT / PAID]
- Open change-order balance: [NONE OR AMOUNT]
- Commercial owner: [NAME]

Handoff does not itself prove payment. Confirm payment directly in Stripe.

---

## 12. Case-Study Permission

Select exactly one:

- [ ] No case-study or publicity permission granted.
- [ ] FieldLookers may use an anonymized description after customer approval.
- [ ] FieldLookers may identify the customer using the restrictions below.
- [ ] Permission will be considered separately and is not granted by this handoff.

Approved uses:

[WEBSITE / PROPOSAL / PRIVATE SALES CONVERSATION / OTHER]

Approved customer name or anonymized description:

[TEXT]

Approved results or metrics:

[TEXT]

Required customer review before publication:

[YES / NO AND CONTACT]

Restrictions or expiration:

[TERMS]

Case-study permission is optional and must not be required for acceptance or handoff.

---

## 13. Referral Request

Referral requested: Yes / No

Request date:

[DATE]

Requested by:

[NAME]

Customer response:

[DECLINED / PENDING / AGREED]

Referral details, if voluntarily provided:

[PRIVATE REFERENCE]

A referral is optional and must not affect acceptance, handoff, support, invoicing, or the customer relationship.

Do not place personal referral information in a public repository.

---

## 14. Customer Handoff Confirmation

Customer or contracting partner confirms:

- [ ] Delivered workflow and artifacts received
- [ ] Operating procedure received
- [ ] Deployment notes received
- [ ] Recovery or rollback boundary understood
- [ ] Known limitations understood
- [ ] Operational ownership accepted
- [ ] Credential ownership accepted
- [ ] Access disposition confirmed
- [ ] Data disposition confirmed
- [ ] Incident contact path understood
- [ ] Support boundary understood
- [ ] Remaining actions recorded below

Remaining actions:

| Action | Owner | Due date |
|---|---|---|
| [ACTION] | [OWNER] | [DATE] |

Customer representative:

- Legal name: [LEGAL NAME]
- Authorized representative: [NAME]
- Title: [TITLE]
- Email: [EMAIL]
- Signature or approved written method: [METHOD]
- Date: [YYYY-MM-DD]

---

## 15. FieldLookers Handoff Confirmation

- Representative: Rafael Morel
- Title: [TITLE]
- Written acceptance verified: Yes / No
- All access items dispositioned: Yes / No
- All data items dispositioned: Yes / No
- Support boundary recorded: Yes / No
- Customer confirmation received: Yes / No
- Signature or approved written method: [METHOD]
- Date: [YYYY-MM-DD]

---

## 16. Final Handoff Checklist

- [ ] Written acceptance attached or referenced
- [ ] Test evidence attached or referenced
- [ ] Delivered artifacts verified
- [ ] Deployment notes complete
- [ ] Operating procedure complete
- [ ] Recovery or rollback instructions complete
- [ ] Known limitations complete
- [ ] Every credential and account has a disposition
- [ ] Every data copy has a disposition
- [ ] Customer operational ownership confirmed
- [ ] Security and incident transition confirmed
- [ ] Support boundary confirmed
- [ ] Final invoice reference recorded
- [ ] Case-study decision recorded
- [ ] Referral decision recorded
- [ ] Remaining actions have owners and dates
- [ ] Customer confirmation recorded
- [ ] Documentation contains no credentials
- [ ] Handoff record stored in the approved private location
