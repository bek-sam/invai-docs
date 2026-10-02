---
name: subprocessor-facts-2026-09
description: Verified sub-processor/vendor state as of 2026-09-28 — no error tracking or analytics tool in code, email provider undecided (OI-13 open), AWS KMS key provisioned but unused.
metadata:
  type: project
---

As of 2026-09-28, verified by reading code directly (not assumed):
- No error-tracking or APM tool (Sentry, Datadog, etc.) and no product-analytics tool (PostHog, etc.) exist
  anywhere in `invai-backend`'s dependencies or code. Don't list one as a sub-processor without re-checking.
- Email provider is still undecided — `invai-backend/src/env.ts` supports any generic SMTP endpoint
  (`SMTP_URL`, `MAIL_FROM`), local dev uses Mailpit, but no production vendor is chosen. See
  `invai-docs/owner-inbox.md` OI-13 (Amazon SES is the leading candidate per product-manager, pending owner
  approval).
- An AWS KMS key is provisioned in `invai-infra/sst.config.ts:58` (`fieldEncryptionKmsKey`) but the app does
  not use it — field encryption runs on its own key ring instead (`invai-backend/src/lib/crypto.ts`). Don't
  claim "KMS encryption" as done; it's provisioned-not-used.
- S&S Activewear credentials are tenant-owned per Shop (no platform-wide key); SanMar is deferred (decision
  0006), not integrated at all.
- Stripe billing is fully stubbed (`env.ts` `mocks.billing`); no real subscription charge exists yet.

**Why this matters:** these are exactly the kind of items that get sloppily marked "done" or invented in a
sub-processor list or security questionnaire. Re-verify before reusing since dates matter (mocks flip to live
as soon as an env var/secret is set) — check `invai-backend/src/env.ts` `mocks.*` fresh each time rather than
trusting this memory alone.

**How to apply:** starting point for any future `subprocessors.md`, `vendor-inventory.md`, or
`security-questionnaire` answer-bank entry — confirm still true, don't copy blindly.

See also [[privacy-retention-code-built]].
