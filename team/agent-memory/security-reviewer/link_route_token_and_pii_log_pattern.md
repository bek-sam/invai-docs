---
name: link-route-token-and-pii-log-pattern
description: T-19-4 (unauthenticated /l/:token email link routes) — where tokens and emails actually leak into logs, and how to prove it
metadata:
  type: feedback
---

When reviewing an unauthenticated, token-bearing public route (ADR 0016 style `/l/:token`
links), don't stop at checking the route's own explicit log lines. Two leak paths that the
in-file logging discipline can't see:

1. **Global `app.onError` handlers that log `c.req.path`.** If the token is a path segment
   (`/l/<token>`), not a query string, then *any* unhandled exception anywhere in the route's
   call chain (a DB hiccup is enough — not hypothetical) gets the token logged verbatim by the
   generic Hono/Express-style catch-all, even though the route's own code never logs it. Proof
   method: `vi.spyOn` a downstream function the handler calls (e.g. `setEmailPreference`) to
   reject, hit the route, and grep the spied `console.error` output for the token substring.
   This is cheap to prove and, when true, is squarely fixable inside the route file itself
   (wrap in try/catch, log ids only) — a good candidate to actually block the card on, even
   when the primary reviewer defers severity to you.

2. **Shared library logging that the feature reuses.** A generic `sendMail`/`mailer.ts` may
   have an old `log.info("mail sent", { to: mail.to })` line that predates the new feature.
   The new feature (e.g. a weekly digest) doesn't add PII logging itself, but it dramatically
   raises the *volume and regularity* of real user emails flowing through that old line. This
   is a legitimate new finding even though the offending line is outside the card's diff and
   outside its owned/grant paths — record it, but don't block the card on it since the fix
   isn't in the card owner's files; route it to the library's owner with a dated clock.

3. **Per-IP rate limits on public routes are only as good as `clientIp()`.** If the IP
   extraction trusts the first `X-Forwarded-For` value with no trusted-proxy check (grep for
   `clientIp` — was already tracked as S-30 in this repo), any new per-IP bucket built on top
   of it is trivially bypassed by rotating the header per request. Check whether this is a
   *new* consumer of an already-known-weak helper — if so, it's worth a cross-reference note
   (extend the existing finding, e.g. S-30 → S-37) rather than a fresh duplicate, but flag that
   the new use case raises the old gap's priority (it may now be the *only* control on an
   endpoint, vs. previously being one of several).

**Process note:** when a shared worktree already has another reviewer's proof-test files sitting
in it (visible via `git status --short`), that's fine — reviewers can run concurrently in the
same worktree per this project's convention (`wave.md`'s ports/DB table only assigns one
worktree slot to "reviewers" collectively). Clean up only the files you added.
