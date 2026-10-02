---
name: ci-deploy-key-restoration-and-trace-pii
description: T-23-7 round 2 CI review pattern — verifying a deploy-key restoration against origin/main and catching a second PII-in-artifact path beyond the one already fixed
metadata:
  type: feedback
---

When a CI card restores a previously-removed control (e.g. deploy keys) under a tech-lead ruling,
diff the restored `with:`/`ssh-key:` block against `git show origin/main:<workflow>` line-for-line
per repo — don't just check "a key exists somewhere". Confirm no repo gained a key it didn't have
before, and that untouched siblings (still missing a credential) were left honestly broken rather
than patched with a new secret.

For a redaction fix (like S-40's `sed` before `tee`), don't just read the regex — trace the real
value's generator (`randomToken()` → `randomBytes().toString("base64url")`) and confirm the
redaction charset actually covers that alphabet. A regex that "looks right" can still miss the
real format.

**Why:** a security fix inside one artifact path (seed stdout → uploaded log file) doesn't cover
a second capture mechanism for the same secret (Playwright `trace: "retain-on-failure"` recording
request headers, including a floor station token, into a separate uploaded artifact). The primary
reviewer flagged this as N3; judge it against the same bounded-blast-radius reasoning already
accepted for the first finding (ephemeral per-job resource, destroyed at job end, private repos,
short retention) rather than re-litigating severity from scratch — file a parallel Low finding
(next `S-NN`) instead of blocking, and don't ask the author to fix Playwright's trace capture
mechanism itself; that is a redesign of a testing tool's own artifact, disproportionate to a Low.

**How to apply:** on any future CI/E2E card, check every place a per-run secret-shaped value
(tokens, PINs, one-time secrets) could be captured, not only the one place a prior review found —
stdout/logs, trace/video recorders, HAR files, screenshot metadata. Each capture path needs its
own bounded-risk judgment, not an assumption that fixing one covers the rest.
