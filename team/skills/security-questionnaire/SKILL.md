---
name: security-questionnaire
description: Answer a security or vendor-risk questionnaire about InvAI (Amazon SP-API control questions, a marketplace or shop vendor review, SIG Lite, CAIQ) from an evidence-backed answer bank, each answer Yes/Partial/No/Not yet with no overstated claims. Use for "security questionnaire", "vendor assessment", "due diligence", "SOC 2?", "how do you protect data".
---

# Security questionnaire

Every questionnaire answer is true today, backed by evidence we could show, reviewed by security, and sent
only by the owner.

## When to use
- A marketplace program asks security questions (Amazon developer profile: answers under 500 characters each;
  TikTok data security review; Walmart; Shopify protected data).
- A larger shop or partner sends a vendor-risk questionnaire.
- The owner needs a short security summary for a sales conversation.

## Steps
1. **Save the questionnaire** (scrubbed of the sender's personal contact details) in
   `invai-docs/compliance/questionnaires/<YYYY-MM-DD>-<requester>/` (created on first use). Note the due date
   and the format limits (character caps, fixed choices).
2. **Open the answer bank** `invai-docs/compliance/questionnaires/answer-bank.md` (to be created on first use
   from [answer-bank.md](answer-bank.md)). Reuse answers; don't write new wording for a question already
   answered.
3. **Answer each question** with:
   - `Status`: `Yes` (control exists, evidence verified), `Partial` (what exists, what's missing), `No`, `Not
     yet — planned <quarter>` (only if a backlog item exists), or `N/A` (reason).
   - `Answer`: short, plain, in the requester's limit.
   - `Evidence`: the file, test, config or doc behind it. Verify it now; bank entries older than 90 days are
     re-checked against code and the DPP pack (`amazon-dpp-evidence-pack`).
4. **Never stretch.** If the true answer is "No", write "No" and, where honest, one line on the plan. Common
   traps for us today (2026-09-24): SOC 2 (none), pen test (none yet), MFA (not yet), centralized 12-month
   logs (not yet), KMS field encryption (key provisioned, not used), written incident plan (not yet). Check
   the current state; these may have closed.
5. **New answers go back into the bank** with the date verified and the evidence path.
6. **Review:** security-reviewer checks every `Yes` and `Partial`; platform-sre checks infra answers.
   Basis: `operating-system.md` "Who reviews whom" (documents are reviewed by one domain owner, plus
   compliance-officer for public claims or legal text); for security claims the domain owner is the
   security-reviewer.
7. **Hand to the owner** with `send-owner-draft`: the filled file, the gaps list, and anything that needs a
   promise (dates) marked `[owner to confirm]`.
8. **Gaps a requester cares about** (they block a deal or approval) go to the PM and tech lead as a proposed
   backlog row (format in `policy-change-watch`).

## Rules (MUST / MUST NOT)
- MUST NOT answer "Yes" without verified evidence. A policy that isn't written, a key that isn't used, or a
  plan in the backlog is not a "Yes".
- MUST NOT claim certifications, audits, pen tests or insurance we don't have. We are not SOC 2 audited;
  research 12 §2.6 is a readiness plan.
- MUST NOT include secrets, internal hostnames, account ids, architecture details beyond what is asked, or any
  PII.
- MUST NOT send or upload the questionnaire. The owner does.
- MUST use InvAI's roles correctly: processor/service provider for buyer data (research 12 §2.4).

## Done when
- Every question has a status, an answer within the requester's limit, and verified evidence or a stated gap.
- security-reviewer approved the Yes/Partial answers.
- The answer bank is updated with new or re-verified answers and dates.
- An `OI-` draft is queued with the file and the gaps list.

## References
- [answer-bank.md](answer-bank.md): starting answer bank by domain
- `invai-docs/research/12-security-quality-playbook.md` (§1 controls, §2 compliance, §7 gaps);
  `invai-docs/security/v1-review.md`
- Amazon developer profile rules: https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer
- Related playbooks: `amazon-dpp-evidence-pack`, `marketplace-app-application`, `legal-doc-draft`,
  `send-owner-draft`
