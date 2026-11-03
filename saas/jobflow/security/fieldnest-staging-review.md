# FieldNest staging security review — 2026-11-03

Status: PR #154 remains draft. No new risk exceptions approved.

## Verified in running staging
- API and migration containers use UID/GID 10001.
- Read-only root filesystem; restricted writable /tmp.
- All capabilities dropped; no-new-privileges enabled.
- API process capability sets are zero; seccomp filtering active.
- Database, migrations, and product readiness passed.
- Synthetic work-order creation and completion passed.

## Separate review image
- Removing mount reduced HIGH findings from 45 to 41.
- Zero CRITICAL findings in the HIGH/CRITICAL scan.
- Archive::Tar did not load; its module file and systemd-homed
  were not found under /usr or /opt.
- SQLite 3.46.1 loads and FTS5 is enabled.
- The review image and running staging image are distinct.

## Outstanding
- All 41 findings remain unresolved under the existing policy.
- No exception dates were extended.
- Staging evidence does not authorize production risk acceptance.
- Assess remaining exposure and evaluate a supported alternative
  runtime image before changing the shared release policy.
