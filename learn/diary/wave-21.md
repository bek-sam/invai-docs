# Wave 21 — evidence and docs (wave 14, part 2)

**Dates:** 2026-09-29. **Pushed:** yes — docs with wave 20, web `3f383e5`.

## What was built
- **T-21-1** Legal drafts for counsel: terms, privacy policy, DPA, sub-processor list,
  vendor inventory (compliance-officer): lawyer-ready drafts, every page marked "Draft,
  pending legal review."
- **T-21-2** Incident-response plan and access-control policy (platform-sre): the written
  policies Amazon, Shopify and pilot shops ask for.
- **T-21-3** Security docs corrected: Amazon 30-day scans, DPP 2025-11, vulnerability SLA
  (security-reviewer): fixing a factual error in the existing security record (Amazon
  wants a vulnerability scan every 30 days, not 180) and mapping the November 2025 Amazon
  data-protection policy changes to what InvAI actually does.
- **T-21-4** Help center en/es and runbook fixes (docs-writer): thirteen help articles in
  both languages, plus runbook corrections.
- **T-21-5** In-app Help and legal links (web-engineer): sign-up shows links to the real
  terms and privacy policy, and the app has a working Help entry.

## Why
A shop can't be onboarded for real — and InvAI can't apply to any marketplace's developer
program — without real policy pages, a real incident plan, and help articles a confused
user can actually open. This wave turns "we know what we'd write" into "it's written,
marked as a draft for counsel where it needs to be, and linked from the app."

## What went wrong
- The incident-response plan needed two review rounds: its first draft contained a wrong
  factual claim (that rotating one secret would be safe) that would actually have broken
  floor PIN logins if followed. Both rounds re-checked the claim against the real code
  before approving it.
- The security record's own prior version had the wrong number for Amazon's scan cadence
  (180 days instead of 30) — a compliance document, like code, can carry its own bug that
  only a dedicated review catches.

## What the team learned
- A policy document that makes an operational claim ("rotating X is safe") needs the same
  verification a code change gets — checked against what the system actually does, not
  what sounds plausible to write.
- Legal and compliance drafts are explicitly marked "Draft, pending legal review" rather
  than presented as finished, and anything needing an owner decision is a visible
  placeholder rather than an invented value — this is now the standing pattern for every
  `legal-doc-draft` output.
- Four Amazon data-protection gaps surfaced by T-21-3 (account lockout, password history,
  18-month data clean-up, required two-step sign-in for owner/admin) were filed as
  backlog items rather than fixed inline here — they matter specifically before an Amazon
  SP-API application, not before this wave's push.

## Files to look at
- `invai-docs/legal/terms.md`, `privacy.md`, `dpa.md`, `subprocessors.md` (en and es) — T-21-1.
- `invai-docs/ops/incident-response.md`, `access-control.md` — T-21-2.
- `invai-docs/security/` — the corrected Amazon scan cadence and DPP mapping (T-21-3).
- `invai-docs/help/{en,es}/` — the thirteen articles (T-21-4).
- `invai-web/src/routes/signup.tsx`, `src/routes/help/`, `src/routes/legal/` — T-21-5.
- `invai-docs/waves/21/owner-report.md` — the full owner-facing account.
