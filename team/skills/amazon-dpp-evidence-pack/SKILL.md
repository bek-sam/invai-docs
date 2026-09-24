---
name: amazon-dpp-evidence-pack
description: Keep InvAI's Amazon SP-API Data Protection Policy (2025-11 update) evidence pack - a control-by-control table of requirement, our evidence, gap, owner and date - so every row is closed before the restricted-role (PII) application. Use for "DPP", "Amazon security review", "SP-API PII", "restricted role", or monthly evidence refresh.
---

# Amazon DPP evidence pack

Every Amazon DPP control has either verified evidence we could show a reviewer today, or a named owner,
backlog item and date.

## When to use
- Before the SP-API restricted-role application (`marketplace-app-application`, Amazon section). All rows must
  be `closed` first (research 12 §2.1).
- Monthly, and after every wave that touched security, logging, retention or infra.
- When Amazon changes the DPP or AUP (`policy-change-watch`), or a reviewer asks a question.
- As the source for `security-questionnaire` answers and the TikTok/Walmart packets, which assume
  Amazon-equivalent controls.

## Where it lives
`invai-docs/compliance/amazon-dpp/evidence-pack.md` (created on first use), plus `evidence/` for screenshots,
config excerpts and test output. Start it from [controls.md](controls.md).

## Steps
1. **Re-read the sources** (dates in the table header):
   - https://developer-docs.amazon/sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy
     (effective 2025-11-25)
   - https://developer-docs.amazon/sp-api/docs/guidance-to-address-key-security-controls-in-sp-api-integration
   - https://developer-docs.amazon/sp-api/docs/vulnerability-management
   New or changed controls get a new row.
2. **Copy [controls.md](controls.md)** into the pack if it doesn't exist. Keep the row ids (D1…); never
   renumber.
3. **Verify each row yourself.** For every "evidence" cell:
   - code: open the file, quote the line, run the test (`cd invai-backend && pnpm test <file>`), paste the
     result line;
   - infra: read `invai-infra/sst.config.ts` and the workflow files; a provisioned resource that the app
     doesn't use is not evidence (the KMS key today);
   - process: the document must exist in `invai-docs/compliance/`, `invai-docs/ops/` or `invai-docs/security/`
     and be dated. A plan in a backlog is not evidence.
   - AWS console facts (log retention, snapshot copies) need the owner or platform-sre: ask for a screenshot
     through the tech lead; mark `waiting on evidence` until then.
4. **Set the status:** `closed` (evidence verified, date), `partial` (what's missing), `open`. Evidence older
   than 90 days gets re-checked.
5. **For each open or partial row,** name the owner role (from the operating-system ownership table), the
   backlog id, and the date Amazon needs it (our target submit date, or the DPP deadline). A gap with no
   backlog id goes to the tech lead as a proposed row (format in `policy-change-watch`).
6. **Check the clocks that are ours to run:** critical vulns ≤ 7 days, high ≤ 30 days, scans every 30 days,
   pen test every 365 days, access review quarterly, LWA secret every 180 days. Write the last and next date
   for each in the pack's "Clocks" section.
7. **Get the review:** security-reviewer checks every `closed` row; platform-sre checks infra rows.
8. **Summarize** at the top: closed / partial / open counts, the critical path to "all closed", and the
   earliest honest application date. Send that summary to the PM and tech lead. If the target date is at risk,
   `escalate-to-owner`.

## Rules (MUST / MUST NOT)
- MUST NOT mark a row `closed` from a doc, a role file or a research note alone. Only code, config, test
  output, a dated written policy or an owner-supplied screenshot count.
- MUST state gaps plainly. The pack is ours, not Amazon's; honesty here prevents a false "yes" later.
- MUST NOT paste secrets, ARNs with account ids, or PII into evidence. Redact to the shape
  (`arn:aws:kms:…:key/…`).
- MUST NOT edit code, infra or security docs to close a row. File the gap to its owner (`respect-ownership`).
- MUST keep the Amazon 24-hour incident notice owned by the human owner (the named IMPOC). Agents draft; the
  owner sends.

## Done when
- Every row in `evidence-pack.md` has a status, verified evidence or a gap with owner, backlog id and date.
- The "Clocks" section shows last and next dates.
- The summary lists counts and the critical path, and security-reviewer has reviewed the closed rows.
- Open gaps are listed in your report.

## References
- [controls.md](controls.md): the starting control table
- `invai-docs/research/12-security-quality-playbook.md` §1.2, §1.4, §1.5, §1.10, §2.1, §2.7, §5;
  `research/10-marketplace-engineering-rules.md` §4 and §9 item 27
- `invai-docs/security/v1-review.md` ("Before applying for Amazon SP-API restricted (PII) access")
- `invai-docs/waves/backlog.md` (B-08, B-09, B-10, B-18, B-21, B-23, B-29)
- Related playbooks: `marketplace-app-application`, `security-questionnaire`, `incident-response`,
  `dependency-and-container-audit`, `backup-restore-drill`
