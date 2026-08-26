# Workflow Automation Credential and Data-Handling Procedure

Version: 1.0  
Status: Initial operating procedure  
Last updated: 2026-08-26  
Owner: FieldLookers LLC

---

## 1. Purpose

This procedure protects provider, partner, end-client, and customer information during Workflow Automation Package delivery.

It applies from discovery through handoff and covers:

- Minimum required access
- Credential transfer
- Test and production separation
- Data collection, storage, retention, and deletion
- Logging and redaction
- Access revocation
- Incident escalation
- Engagement evidence

Every engagement must complete the pre-access, active-delivery, and handoff checklists in this procedure.

This procedure does not replace customer-specific contractual, legal, regulatory, insurance, or security requirements. Additional requirements must be documented in the Statement of Work before access is granted.

---

## 2. Governing Principles

### Least privilege

Request only the systems, permissions, data, and duration required for the approved deliverables.

### Customer authorization

The customer or contracting partner must confirm that it has authority to provide every account, credential, system, and dataset used during delivery.

### Named access

Prefer a named FieldLookers account over shared credentials.

### Test before production

Use sanitized test data and non-production environments whenever practical.

### No secrets in communication records

Credentials and secrets must never appear in:

- GitHub issues or comments
- Source control
- Documentation repositories
- Email bodies or attachments
- Ordinary chat or messaging threads
- Screenshots
- Meeting notes
- Application logs
- Terminal transcripts retained as engagement evidence

### Defined disposition

Before access is granted, every credential and data copy must have an identified owner, approved location, purpose, and handoff or deletion action.

### Stop when unsafe

If access or data cannot be handled safely, lawfully, or within the approved scope, delivery pauses until the parties approve a safe alternative.

---

## 3. Roles and Responsibilities

### Customer or contracting partner

The customer or partner must:

- Identify the workflow owner
- Identify the access authorizer
- Confirm authority over systems and data
- Create or approve required accounts
- Provide the minimum necessary permissions
- Classify sensitive and prohibited data
- Approve production access
- Identify incident-response contacts
- Review access during handoff
- Revoke, transfer, or confirm continued access
- Approve retention and deletion outcomes

### FieldLookers

FieldLookers must:

- Request only minimum necessary access
- Use only approved access methods
- Keep credentials outside source control and ordinary communications
- Prefer sanitized test data
- Separate test and production activity
- Redact sensitive values from logs and evidence
- Report suspected exposure through the incident path
- Remove working data and access according to the approved disposition
- Record completion without recording secrets

### End client, if applicable

When an IT provider or partner retains the end-client relationship, the Statement of Work must identify whether the partner or end client:

- Authorizes system access
- Supplies accounts or data
- Approves production changes
- Receives incident notices
- Accepts delivery
- Revokes access after handoff

FieldLookers must not infer end-client authorization from the partner relationship alone.

---

## 4. Engagement Security Record

Create a private engagement security record before requesting access.

Record:

- Engagement reference:
- Customer or partner:
- End client, if applicable:
- Workflow:
- Workflow owner:
- Access authorizer:
- Data owner:
- Acceptance approver:
- Primary incident contact:
- Backup incident contact:
- Approved communication channel:
- Approved secure-transfer system:
- Test environment:
- Production environment:
- Retention decision:
- Planned handoff date:
- Access-review date:
- Deletion-verification date:

The record may identify systems and account owners but must not contain passwords, tokens, recovery codes, private keys, connection strings, session cookies, or secret values.

Public repository evidence must use anonymized identifiers.

---

## 5. Access Inventory

Document every required system before access is granted.

| System | Environment | Business purpose | Requested role | Account owner | Authorizer | Expiration or review date |
|---|---|---|---|---|---|---|
| [SYSTEM] | Test/Production | [PURPOSE] | [ROLE] | [OWNER] | [AUTHORIZER] | [DATE] |

For each entry, confirm:

- [ ] The system is explicitly included in the SOW
- [ ] The customer has authority to grant access
- [ ] The requested permission is the minimum required
- [ ] A named account will be used when supported
- [ ] Multi-factor authentication is enabled when supported
- [ ] Production access is separately justified
- [ ] The account has an expiration or review date
- [ ] The revocation owner is known

Do not request full administrative access merely because it is easier.

If a platform cannot provide suitably limited access, record the constraint and obtain written approval before proceeding.

---

## 6. Approved Credential-Transfer Methods

Use these methods in order of preference.

### Method 1 — Vendor-native invitation

Preferred method:

1. Customer creates a named FieldLookers user through the system’s administrative interface.
2. Customer assigns the minimum required role.
3. The vendor sends the account invitation directly.
4. FieldLookers creates its own password and enables multi-factor authentication.
5. Customer retains the ability to revoke the account.

No secret is transmitted between the parties.

### Method 2 — Approved password-manager secure share

Use only when a vendor-native invitation is unavailable.

Requirements:

- The exact password manager or encrypted sharing system is recorded in the engagement security record.
- The share is restricted to the intended recipient.
- The share expires or supports one-time retrieval.
- The retrieval link is delivered through the verified engagement channel.
- Any access password or verification code is communicated through a separate verified channel.
- FieldLookers moves the secret into its approved credential store immediately.
- The temporary share is revoked or allowed to expire.
- Multi-factor authentication and recovery ownership are documented.

### Method 3 — Customer-operated supervised access

Use when credentials must not be transferred.

Examples:

- Customer shares its screen and performs the privileged step.
- Customer enters the secret directly into the approved configuration surface.
- Customer executes a reviewed command.
- Customer creates a scoped token and enters it without exposing the value.

### Prohibited methods

Do not accept or transmit credentials through:

- GitHub
- Source files
- `.env` examples containing real values
- Email
- Unencrypted documents
- Ordinary SMS or chat
- Recorded video
- Screenshots
- Public forms
- Support tickets
- Terminal output retained in project records

If a secret arrives through a prohibited method:

1. Stop using the exposed secret.
2. Notify the sender through the incident contact path.
3. Ask the system owner to rotate or revoke it.
4. Remove unnecessary copies when authorized.
5. Record the exposure without copying the secret.
6. Resume only after safe replacement access is confirmed.

---

## 7. Credential Storage and Use

FieldLookers must:

- Store credentials only in an approved credential manager or protected runtime-secret mechanism
- Keep secrets separate from application source
- Use environment or deployment-secret configuration where supported
- Prevent secrets from appearing in command history
- Avoid printing environment variables, tokens, headers, or connection strings
- Use separate credentials for test and production
- Never reuse customer credentials for another engagement
- Never reuse FieldLookers production credentials in customer environments
- Never disclose provider secrets to a customer, partner, browser frontend, or public repository

Credential records should identify:

- System
- Account name
- Credential owner
- Environment
- Purpose
- Creation date
- Review date
- Revocation owner

The record must not reproduce the secret.

---

## 8. Test and Production Separation

### Default rule

Use this order:

1. Local or isolated development environment
2. Sanitized test data
3. Vendor sandbox or customer test environment
4. Controlled production verification only when required

### Test access

Test environments must use:

- Test-only accounts
- Test-only credentials
- Sanitized or synthetic data
- Non-production endpoints when available
- Clearly labeled test outputs

### Production access

Production access requires all of the following:

- [ ] Explicit SOW requirement
- [ ] Written customer authorization
- [ ] Verified backup or recovery path when a change can affect data
- [ ] Approved change window
- [ ] Named operator
- [ ] Minimum required role
- [ ] Defined verification steps
- [ ] Defined rollback or safe-stop procedure
- [ ] Incident contacts available
- [ ] Post-change evidence that excludes secrets and unnecessary customer data

Do not use production as a development or experimentation environment.

---

## 9. Data Inventory and Classification

Document only the data needed for the approved workflow.

| Data category | Owner | Environment | Sensitivity | Purpose | Approved location | Retention |
|---|---|---|---|---|---|---|
| [CATEGORY] | [OWNER] | Test/Production | [LEVEL] | [PURPOSE] | [LOCATION] | [PERIOD/ACTION] |

Classify data as:

### Public

Information intentionally available to the public.

### Internal

Non-public operational information that does not normally require heightened protection.

### Confidential

Customer records, partner information, business processes, internal reports, or other information restricted to authorized participants.

### Restricted

Credentials, authentication material, regulated data, financial account information, highly sensitive personal data, security material, or data whose exposure could create substantial harm.

Restricted data requires explicit approval and additional handling terms. FieldLookers may decline work requiring restricted data that it is not prepared or authorized to handle.

---

## 10. Data-Minimization Rules

FieldLookers must:

- Collect only fields required for the approved workflow
- Prefer representative subsets over complete datasets
- Prefer sanitized or synthetic data
- Avoid copying production data when read-only access or customer-executed testing is sufficient
- Avoid retaining raw inputs after transformed or redacted evidence is sufficient
- Exclude unrelated records
- Avoid downloading entire databases or mailboxes for convenience
- Remove secrets from configuration samples
- Avoid placing customer names or identifiable records in public evidence

When uncertain whether data is required, do not collect it until the owner confirms the purpose and approval.

---

## 11. Approved Storage and Transfer

The engagement security record must identify every approved storage and transfer location.

Approved locations may include:

- Customer-controlled system
- Customer-approved FieldLookers working environment
- Approved encrypted credential manager
- Approved encrypted transfer mechanism
- Contractually approved deployment environment

Do not place customer data in:

- Public repositories
- Personal notes unrelated to the engagement
- Unapproved cloud storage
- Public paste services
- Ordinary email attachments
- Unapproved AI or third-party services
- Test systems shared with unrelated projects

Before using any third-party service with customer data, confirm authorization, necessity, applicable terms, and deletion capability.

---

## 12. Logging, Evidence, and Redaction

Logs and engagement evidence may record:

- Timestamp
- System name
- Non-sensitive operation
- Success or failure state
- Sanitized error category
- Approved anonymized record identifier
- Operator
- Corrective action

Logs and evidence must not record:

- Passwords
- Tokens
- API keys
- Private keys
- Recovery codes
- Session cookies
- Authorization headers
- Full connection strings
- Raw payment data
- Unnecessary personal data
- Complete customer payloads
- Confidential message contents unless specifically approved

Before sharing logs or screenshots:

1. Review the entire artifact.
2. Remove secrets and authentication material.
3. Redact unrelated customer information.
4. Crop unnecessary interface areas.
5. Confirm browser tabs, addresses, filenames, and notifications reveal nothing sensitive.
6. Store the sanitized artifact only in the approved engagement location.

If safe redaction cannot be confirmed, do not share the artifact.

---

## 13. Development and Source-Control Rules

- Real secrets must never be committed.
- Customer data must not be used as test fixtures unless sanitized and expressly approved.
- `.env` examples must contain placeholders only.
- Generated build artifacts must not embed production configuration.
- Branches, commit messages, pull requests, issues, and test output must not contain sensitive customer information.
- Temporary debug output must be removed before commit.
- Secret-scanning findings must be investigated before delivery.
- A secret committed at any point must be treated as exposed even if the commit is later deleted.

If a secret enters source control:

1. Stop affected work.
2. Revoke or rotate the secret.
3. Notify the approved incident contact.
4. Remove the secret from active files.
5. Determine whether repository-history remediation is required.
6. Document the incident without reproducing the secret.

---

## 14. Retention and Deletion

### Required engagement decision

The SOW or engagement security record must define:

- What data FieldLookers may retain
- Business and contractual purpose
- Approved storage location
- Retention period or deletion trigger
- Backup implications
- Person authorized to request deletion
- Person responsible for deletion
- Evidence required to confirm disposition

### Default working-copy rule

When no longer required for delivery, acceptance, a separately agreed correction period, or a documented legal obligation, FieldLookers will delete its unnecessary working copies.

Unless the SOW states a different reviewed period, unnecessary working copies should be removed within five business days after handoff and written acceptance.

Do not promise immediate deletion from immutable backups or third-party systems unless that capability has been verified. Backup treatment must be documented separately when applicable.

### Deletion verification

Record:

- Data category:
- Approved deletion authority:
- Locations reviewed:
- Deletion date:
- Operator:
- Backup or archive treatment:
- Exceptions:
- Customer confirmation required: Yes / No
- Verification evidence location:

Do not copy deleted data into the deletion record.

---

## 15. Incident Identification and Escalation

A suspected incident includes:

- Credential sent through a prohibited channel
- Secret exposed in logs, source control, screenshots, or recordings
- Unauthorized account use
- Access beyond approved scope
- Customer data sent to an unintended recipient
- Lost device or compromised account
- Unapproved production change
- Data retained beyond the approved period
- Malware, suspicious authentication, or unexpected system behavior
- Inability to account for a customer data copy

### Immediate response

1. Stop the affected activity.
2. Preserve only the evidence needed for safe investigation.
3. Contain exposure when authorized.
4. Revoke or rotate affected credentials through the system owner.
5. Notify the FieldLookers engagement owner.
6. Notify the customer’s primary incident contact through the approved channel.
7. Escalate to the backup contact if the primary contact is unavailable.
8. Record known facts, affected systems, time, containment, and decisions.
9. Do not speculate or admit conclusions before facts are verified.
10. Resume only after the authorized parties approve the recovery path.

### Contact path

Every SOW or engagement security record must identify:

- Customer primary incident contact
- Customer backup incident contact
- FieldLookers engagement owner
- Approved urgent communication channel
- Vendor or partner escalation contact, if applicable
- Contractual or legal notification requirements

Do not use a public GitHub issue for incident coordination.

Required notification timing must follow the applicable agreement and qualified legal guidance. Do not invent a notification promise during delivery.

---

## 16. Access Review During Delivery

Review access:

- Before first use
- When scope changes
- When a team member changes
- Before production work
- At acceptance
- At handoff
- When suspicious activity occurs

Review questions:

- Is the account still required?
- Is the permission still minimal?
- Is the correct person using it?
- Has the password, token, role, or vendor policy changed?
- Is production access still justified?
- Is the expiration date still appropriate?
- Does the SOW still authorize the activity?

Remove access that no longer has a documented purpose.

---

## 17. Handoff and Access Disposition

Handoff is incomplete until every access and data item has a recorded disposition.

Allowed access outcomes:

- Revoked
- Transferred to the customer
- Retained under a separate written support agreement
- Expiring automatically on a confirmed date

Allowed data outcomes:

- Returned
- Deleted
- Retained for a documented purpose and period
- Remains solely in the customer-controlled system

Handoff record:

| Item | Owner | Outcome | Completed by | Date | Verification |
|---|---|---|---|---|---|
| [ACCOUNT OR DATA] | [OWNER] | [OUTCOME] | [PERSON] | [DATE] | [EVIDENCE] |

At handoff, confirm:

- [ ] Customer operational owner identified
- [ ] Customer credential owner identified
- [ ] FieldLookers named accounts revoked or disposition documented
- [ ] Shared credentials rotated by the system owner
- [ ] Temporary tokens revoked
- [ ] Temporary secure shares expired or revoked
- [ ] Production access removed unless separately authorized
- [ ] Working data returned, deleted, or retained under written terms
- [ ] Test data disposition recorded
- [ ] Local and temporary storage reviewed
- [ ] Logs and screenshots reviewed for sensitive information
- [ ] Backup implications recorded
- [ ] Known limitations documented
- [ ] Incident contacts confirmed for any correction period
- [ ] Customer or partner confirms the disposition

---

## 18. Pre-Access Checklist

Complete before FieldLookers receives access or customer data:

- [ ] Final SOW approved
- [ ] Workflow and systems are in scope
- [ ] Customer authorization confirmed
- [ ] Access authorizer identified
- [ ] Data owner identified
- [ ] Incident contacts identified
- [ ] Minimum permissions defined
- [ ] Named accounts requested where supported
- [ ] Test environment evaluated
- [ ] Sanitized test data evaluated
- [ ] Production access separately justified
- [ ] Secure-transfer method recorded
- [ ] Approved storage locations recorded
- [ ] Data categories and sensitivity recorded
- [ ] Prohibited data recorded
- [ ] Retention and deletion decision recorded
- [ ] Revocation owner and review date recorded
- [ ] Legal, contractual, vendor, and end-client approvals confirmed
- [ ] No credentials have been placed in ordinary communications or repositories

If any required control is unresolved, do not receive access or data.

---

## 19. Active-Delivery Checklist

- [ ] Access remains minimum and authorized
- [ ] Test and production credentials remain separate
- [ ] Customer data remains in approved locations
- [ ] Secrets remain outside source control and logs
- [ ] Evidence is anonymized or redacted
- [ ] Scope changes receive written approval
- [ ] Temporary data is removed when no longer required
- [ ] Access inventory remains current
- [ ] Incident contacts remain reachable
- [ ] Any suspected exposure is escalated

---

## 20. Handoff Checklist

- [ ] Acceptance decision recorded
- [ ] Access inventory reviewed
- [ ] Every account has a disposition
- [ ] Every credential has an owner
- [ ] Shared credentials rotated when applicable
- [ ] Temporary credentials and tokens revoked
- [ ] Production access removed or separately authorized
- [ ] Every data copy has a disposition
- [ ] Retention and deletion actions completed or scheduled
- [ ] Backup implications documented
- [ ] Logs and evidence reviewed
- [ ] Documentation contains no secrets
- [ ] Operational ownership transferred
- [ ] Ongoing support access governed by a separate agreement
- [ ] Customer or partner confirms access and data disposition

---

## 21. Engagement Completion Evidence

Record without including secrets or unnecessary customer data:

- Engagement reference:
- SOW approval date:
- Access authorizer:
- Approved transfer method:
- Test access used: Yes / No
- Production access used: Yes / No
- Production authorization reference:
- Acceptance date:
- Handoff date:
- Accounts revoked:
- Accounts transferred:
- Accounts retained under support agreement:
- Working-data deletion date:
- Retained-data purpose and deadline:
- Incident count:
- Unresolved security actions:
- Customer confirmation reference:
- FieldLookers operator:
