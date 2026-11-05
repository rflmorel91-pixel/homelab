# Session lifecycle

Browser sessions use a Secure, HttpOnly, SameSite=strict cookie. API bearer
tokens use the same authentication checks and revocation generation.

- Login starts a new authentication period.
- Tokens expire after 30 minutes. Authenticated cookie requests renew this
  idle window, retaining the original signed `auth_time`.
- Every session requires fresh login eight hours after that authentication
  time. Renewal cannot extend the absolute deadline; the cookie and JWT are
  capped to it. Bearer tokens are validated against the same deadline.
- Logout increments the account's `session_version` atomically. It signs out
  **all devices and product workspaces for that account**, including copied
  tokens and renewed cookies. In-flight requests that already authenticated
  may finish; future authentication rejects the revoked generation.
- Anonymous, malformed, expired and already revoked logout requests still
  clear the caller's cookie and return `signed_out`. They do not revoke a
  newer login generation.
- Password reset continues to invalidate earlier session generations.

## Compatibility and rollout

No database migration or dependency change is required. The existing
`users.session_version` column supplies revocation.

Existing signed tokens without `auth_time` use their signed `iat` as the
authentication time. The first renewal preserves it as `auth_time`. Tokens
must contain `sub`, `iat` and `exp`. Existing token helper functions keep
their previous return values for callers.

Deploy API workers together. An old worker retains the old logout/renewal
behavior and cannot enforce the new absolute lifetime. Rolling back code
reintroduces that limitation; do not decrement session versions or restore
the database just to roll back this application change.

Per-device logout would require a separate session registry. Account-wide
revocation deliberately reuses the current schema for this fix.

## Verification

Run the isolated real-router/JWT regression checks without PostgreSQL:

```bash
python -B tests/test_session_security.py
```

These use synthetic users in an in-memory SQLite database. They exercise
cookie and bearer replay after logout, other devices, repeated/stale logout,
fresh login, continuous renewal up to the absolute deadline, one-second cookie
expiry, legacy tokens, malformed/missing claims, idle expiry and the password
reset revocation generation.

The normal `pytest -q` PostgreSQL suite also collects these checks and includes
a replay regression using the full application and PostgreSQL fixtures in
`tests/test_auth.py`. Existing password-reset tests cover reset delivery and
session invalidation end to end.

After release, use a synthetic account to check login, logout, re-login and
access to each active product. Never print or share session tokens in logs,
shell history, screenshots or acceptance evidence.
