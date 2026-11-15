# FieldNest property editing

This release changes both the API and workspace frontend. It adds no tables or migrations. `PATCH /api/v1/products/fieldnest/properties/{id}` updates supplied name, address, unit count and property type fields within the authenticated current tenant. Unknown fields and explicit nulls are rejected; another tenant's property returns 404.

## Deployment order

1. Prepare and test an API candidate based on the actual running release, preserving private billing extensions and the existing production configuration. Do not replace the current API image with an unverified build from public main. Record the old image ID and effective Compose overrides for rollback.
2. Deploy the API to isolated staging first. Verify a same-tenant edit, rejection of invalid values and another tenant's ID, and unchanged linked residents, work orders, maintenance plans and resident request links.
3. Prepare a frontend candidate against the actual active workspace, preserving its billing additions. Activate only after the matching API is available.
4. In staging, edit each field, reopen to check saved values, cancel a dirty edit, test a failed save, and switch workspace/sign out while a save is pending. Verify refreshed property names in linked work orders and selectors. Existing records must keep their IDs.
5. Obtain production release approval for the tested backend and frontend candidates. Retain the previous image and HTML/assets, deploy API before frontend, verify the same acceptance journey and run the existing cloud backup/restore verification service.

## Rollback

Restore the previous workspace HTML/assets to hide the editor, then restore the recorded API image using the effective Compose configuration. Property corrections already saved remain in the database; reverting code does not reverse them. No database downgrade is required.

## Validation

The focused API suite uses an isolated SQLite database with foreign keys and the real API router, checking identity/link preservation, tenant boundaries, input validation, partial/no-op patches and transaction rollback. PostgreSQL integration and migration checks remain CI gates. The frontend VM suite exercises the shipped editor's payload, duplicate guard, retained drafts, unsaved dismissal and stale-response guards; browser acceptance remains required.
