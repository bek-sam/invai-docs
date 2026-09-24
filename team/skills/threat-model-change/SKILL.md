---
name: threat-model-change
description: Threat-model an InvAI change before it is built. Who can call it, with which session (user, floor, station token, vendor, webhook, job), against whose data, and what the worst outcome is, then map each threat to a control and a test. Use for cards flagged tenancy, pii, auth, webhooks, files, payments or ai, for new integrations, and when someone asks "is this safe" or "threat model".
---

# Threat-model a change

Before code is written, every way the change could leak a tenant's data, escalate a role, double a side effect
or burn money is named, with the control and the test that stop it.

## When to use
- Any card with risk flags `tenancy`, `pii`, `auth`, `webhooks`, `files`, `payments` or `ai` (at
  `task-intake`, before coding).
- A new marketplace, carrier or supplier integration, a new AI route or tool, a new file type, a new public
  endpoint.
- A security-reviewer co-review, if no threat model exists yet.

## Steps
1. **Copy the template** from this folder into your report draft, or, for the security-reviewer, into
   `invai-docs/security/threat-models/T-<n>-<k>.md` (folder to be created, owned by security-reviewer).
2. **List the entry points.** From the contract (`invai-contracts/src/contract/<area>.ts`): each procedure's
   `auth` kind and `permission`. Plus webhooks (`invai-backend/src/api/webhooks.ts`), jobs (`defineJob` in
   `src/modules/<area>/jobs.ts`), SSE (`src/api/events.ts`) and imaging endpoints
   (`invai-imaging/app/main.py`, no auth today: internal-only, research 12 G4).
3. **Say where the tenant comes from** for each entry point. It must come from the session or the matched
   connection, never from a request body or an unverified webhook payload (research 12 §1.1 "Workers enter the
   tenant too").
4. **List the data touched** and mark PII: `buyer_pii` fields, `orders.buyer_note`, `buyerName`, label PDFs,
   CSV uploads, raw payloads, channel credentials. Check that PII is encrypted (`encryptedText`), covered by
   the purge (`purgeBuyerPii`, `purgePiiObjects` in `src/modules/orders/jobs.ts`), and returned only with the
   right permission (`shipTo` needs `orders.manage`).
5. **Walk the 10 threats** in the template. For each, find the control in code (`file:line`) and the test that
   proves it. Useful greps:
   ```
   grep -rn "withSystem(" invai-backend/src --include=*.ts | grep -v test
   grep -rn "isCompanyKey\|isSafeKey" invai-backend/src/modules
   grep -rn "permission:" invai-contracts/src/contract/<area>.ts
   grep -rn "timingSafeEqual" invai-backend/src
   ```
6. **Write the worst outcome** in one sentence, with blast radius (one user, one shop, every shop). This sets
   severity: cross-tenant access, auth bypass or a PII leak is **High**
   (`.claude/agents/security-reviewer.md`).
7. **Turn gaps into acceptance criteria.** Each gap becomes a Given/When/Then on the card (ask the tech lead
   to add it) and a test at the lowest layer: a cross-tenant `NOT_FOUND` test for the implementer's own
   tables in the module's normal tests (`security.test.ts` belongs to security-reviewer; the implementer
   doesn't edit it), a permission case covered by `src/api/authz.test.ts`, a run-twice test for side
   effects, an injection-string eval for AI routes.
8. **Decide and record.** Required controls go on the card. An accepted risk goes in
   `invai-docs/security/v1-review.md` as a finding (id, severity, area, description, status, owner) through
   the security-reviewer. A High that you want to accept needs the owner (`escalate-to-owner`).
9. **Get the security-reviewer's verdict** on the threat model before the build starts for tenancy, pii, auth,
   webhooks, files or payments flags.

## Rules
- MUST treat every marketplace text field (titles, SKUs, buyer notes, personalization) as untrusted input,
  including in AI prompts (research 12 §1.9).
- MUST keep cross-tenant answers `NOT_FOUND`, never `FORBIDDEN`, so a response never reveals that a row
  exists.
- MUST verify webhook signatures on the raw body before enqueueing anything (S-28).
- MUST NOT accept a fail-open control on a security path without a warn log and an alert (research 12 §1.10
  A10).
- MUST NOT weaken an existing control to make the change easier. Propose a safer alternative, or escalate.

## Done when
- The template is filled: entry points, data, all 10 threats with control + test or "n/a" with a reason, worst
  outcome.
- Every gap is an acceptance criterion on the card or a recorded finding with an owner.
- The security-reviewer has given a verdict for the high-risk flags.

## References
- `template.md` (this folder)
- `invai-docs/research/12-security-quality-playbook.md` §1 (checklists), §4 (review checklist), §7 (known gaps
  G1–G14)
- `invai-docs/security/v1-review.md` (findings S-01 to S-32 and what was verified)
- `.claude/agents/security-reviewer.md` (severity, controls in place)
- Related: `tenant-isolation-audit`, `idempotent-side-effect`, `ai-feature-with-evals`
