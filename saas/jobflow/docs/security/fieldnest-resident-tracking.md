# Resident tracking and photos

## Access and privacy

Each new form submission generates a random 32-byte tracking secret in the
resident browser. The server stores only its SHA-256 hash and a 90-day expiry.
The successful report response returns a private /fieldnest/resident fragment
link when the supplied secret matches that report. Retries reuse the same
submission ID and secret; they do not duplicate work orders or photos.

The private link opens one request's title, unit, current status, timestamps and
resident-submitted photos. It does not expose contact details, descriptions that
may contain internal notes, vendor records or other residents' requests.
Anyone with the private link can view that request; this is bearer access, not
verified resident identity. Owners can replace or disable each tracking link.

The shared property intake link grants no access to existing requests or photos.
Disabling that shared intake link does not disable private tracking links for
previous reports; owners manage those links separately in work-order details.
Suspending a company/product or expiring/revoking a tracking link blocks its use.

Private secrets stay in URL fragments and API request bodies, not URL paths or
query strings. Public reads are POST requests with credentials omitted and
Cache-Control: no-store. Photo bytes require the same request secret; guessing
another photo ID does not grant access. Manager photo routes also validate both
the authenticated company and work-order scope.

Tracking links are intentionally not inserted into email receipts because only
their hashes are retained. Residents should save the link shown after submission;
owners can issue a replacement if it is lost. Existing reports without tracking
secrets can receive a replacement through the owner's controls.

## Photo processing and storage

- At most three JPEG/PNG still images per initial report.
- Each input is at most 2 MiB and 12 million pixels. The server validates and
  fully decodes the image; filename and browser MIME assertions are insufficient.
- Photos are oriented, resized, converted to fresh pixel-only JPEGs, and bounded
  to 512 KiB each. EXIF/GPS, comments and other source metadata are discarded.
- Two normalization slots per API process bound concurrent decoder memory.
- A company has a 100 MiB photo budget. PostgreSQL tenant-row locking serializes
  quota decisions. Reports without photos remain available when the budget is full.
- Photos are private BYTEA database records, included in database backups.
  They are not placed in public static directories or a new filesystem volume.
- Deleting a work order cascades deletion of its photos. Backup retention still
  governs copies in backups.

Photos in this version are resident-supplied attachments. Do not use the same
publicly viewable photo path for internal-only manager attachments.
Additional resident comments, after-submission uploads, completion photos and
resident accounts are not implemented.

Nginx accepts up to 9 MiB for the base64 JSON intake body, retaining its existing
intake rate limit. Tracking has a separate 30/minute/IP limit with burst 10.
Only FieldNest image display pages allow local blob image URLs; scripts remain
restricted to same-origin external files.

## Dependency and migration

Pillow 13.0.0 is pinned in both dependency declarations. The Alpine image adds
JPEG/zlib build and runtime support. This shared image must be rebuilt.

Migration a6c8e0f2b415 follows e4b6d8f0a213. Existing work orders remain intact and
receive nullable tracking fields. The new photo table uses company/work-order
foreign keys and deletion cascade. Downgrade removes photos and tracking access;
preserve required images before a downgrade.

## Validation and remaining acceptance

Thirteen focused tracking/photo tests passed, including private scope, status
refresh, expiry, replacement/revocation, photo normalization, invalid inputs,
image dimensions, quota and duplicate submissions. Existing resident form,
email and workspace race checks passed. The PostgreSQL upgrade SQL was generated
and checked; the product contract and syntax checks passed.

Full CI, PostgreSQL quota concurrency/migration drift, Nginx runtime checks and
visual mobile/browser verification still require staging. SQLite tests do not
exercise PostgreSQL row locking.

## Primary dependency references

- https://pypi.org/project/pillow/13.0.0/
- https://pillow.readthedocs.io/en/stable/reference/Image.html
