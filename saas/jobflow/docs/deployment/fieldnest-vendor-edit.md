# FieldNest vendor editing

Edit existing vendor names, trades, optional phone/email details and recorded insurance expiry. The tenant-scoped PATCH endpoint updates the original vendor row; existing work orders and maintenance plans keep their vendor IDs. Omitted fields are preserved. Explicit nulls clear optional fields; blank phone/email strings are normalized to null. Name and trade cannot be null or blank. Unknown fields, including IDs and tenant IDs, are rejected.

## Release order

This changes the API and workspace frontend, with no schema migration. Prepare the API candidate from the actual running private billing release, preserving its existing code and dependencies. Do not replace it blindly with a public-main build. Verify the vendor PATCH route and existing property-edit/billing routes before activating the editor frontend. Prepare frontend candidates surgically against the active workspace and stylesheet to retain billing additions and the existing disabled Clear filters cursor fix.

Retain the current API image ID, effective Compose configuration, HTML and fingerprinted assets for rollback. Activate the API first, verify readiness, then activate the frontend after staging acceptance and production approval. Preserve the new API override in deployment entry points. Rebuilding an older non-Git backend source directory will not automatically contain this release.

## Browser acceptance

Use a synthetic staging vendor assigned to an existing work order and maintenance plan. Open Edit vendor and check every saved field. Change its name, trade, phone/email and expiry; save, reopen and refresh. Verify the same vendor remains assigned, labels/selectors reflect the update and active filters/counts are reevaluated. Clear optional fields and verify the new no-expiry label/filter after saving. Confirm failed saves retain drafts, duplicate submission is guarded, edits cannot continue during a save, close/Escape asks before discarding a changed draft, and workspace changes/sign-out prevent stale save responses from repopulating the old editor.

Insurance expiry remains a recorded date, not verified coverage. Editing it neither sends reminders nor changes assignments.

## Validation and rollback

The isolated API suite checks partial updates, assignment preservation, tenant boundaries, input bounds, clearing optional fields, no-op updates and commit failure. The frontend regression exercises the shipped editor's prefill/payload, save guards, draft retention, clearing, retry and close/workspace races. Browser acceptance and PostgreSQL integration/migration CI remain additional gates.

For rollback, restore the prior frontend HTML/assets before restoring the recorded previous API image using its effective configuration. Saved vendor corrections remain in the database when code is rolled back. No database downgrade is required. Finish release acceptance with the existing cloud backup/restore verification; back up a newly deployed API image and configuration separately as required by the recovery process.
