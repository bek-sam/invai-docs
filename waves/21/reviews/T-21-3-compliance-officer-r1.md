# T-21-3 review (round 1) — compliance-officer (co-reviewer)

Card: `invai-docs/waves/21/T-21-3.md`. Commit: `ed0ef87` (invai-docs). Author report:
`invai-docs/waves/21/reports/T-21-3.md`. Read-only review; no commit, no push.

## Verdict: Approve

## What I checked

### 1. Amazon SP-API documentation, fetched live 2026-09-28

| Page | Claim in the commit | What the live page says | Match |
|---|---|---|---|
| `.../sp-api/docs/vulnerability-management` | scan every 30 days, code scan before every release, pen test every 365 days, critical ≤7d, high ≤30d | "Conduct vulnerability scans every 30 days." / "Scan code for vulnerabilities prior to every release." / "Conduct penetration tests every 365 days." / "Resolve critical-risk vulnerabilities within seven days of discovery." / "Resolve high-risk vulnerabilities within 30 days of discovery." | Exact |
| `.../sp-api/docs/guidance-to-address-key-security-controls-in-sp-api-integration` | MFA "for all accounts that use approved second factors (TOTP, hardware tokens, or biometric authentication)"; monthly scanning; annual pen test | "Deploy Multifactor Authentication (MFA) for all accounts that use approved second factors (TOTP, hardware tokens, or biometric authentication)." / "Conduct vulnerability scanning at least every 30 days..." / "annual penetration testing..." | Exact |
| `.../sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy` | 2025-11-25 DPP/AUP update: account lockout after 10 failed logins, password history (last 10), non-PII ≤18 months, log retention 12 months, TLS 1.2+/KMS, anti-malware disablement controls, critical/high SLAs, geo-dispersed backups, IMPOC, third-party risk assessments, terminology change | All eleven items confirmed verbatim on the live changelog page, effective 2025-11-25. MFA is correctly *not* claimed as part of this changelog entry — the commit sources MFA separately from the key-security-controls page and labels the table row accordingly ("key-security-controls guidance, tied to the DPP") rather than misattributing it | Exact |

No discrepancies found in any cited quote, cadence number or SLA. The author's own citation practice (quoting, not paraphrasing, with access date) held up against a fresh fetch.

### 2. Each DPP 2025-11-25 row's requirement and InvAI's gap

Spot-checked the highest-risk rows against code, read-only:
- **Account lockout**: `grep -rn "lockout\|failedAttempts\|failedLogin\|accountLock" src` finds only the floor-PIN station lockout (S-06); email/password sign-in has IP rate limiting (`src/auth.ts:231`, 20/min) but no separate per-account counter. Row correctly marked open.
- **Password history**: no match anywhere in `invai-backend/src` for password-reuse history. Row correctly marked open.
- **Non-PII ≤18 months**: `BUYER_PII_RETENTION_MONTHS = 18` (`src/modules/privacy/service.ts:285`) redacts buyer *PII* on old orders — it does not cap retention of non-PII order data/metrics. The table correctly distinguishes "S-16 covers PII only" and marks the non-PII sweep open, not falsely closed by reusing the PII figure.
- **MFA for owner/admin**: `twoFactor` plugin is wired (`src/auth.ts:378-381`) but no code path requires `twoFactorEnabled` for an owner/admin role; grep for `requireTwoFactor`/`mfaRequired` finds nothing. Row correctly marked open, and the table correctly notes it's "optional" rather than claiming a false pass.
- **Backups (geo-dispersed)**: `invai-infra/sst.config.ts` was read-only checked; no cross-region snapshot copy found. Row correctly routed to platform-sre with no false "closed".

Every row I checked cites real file:line or states "not found" — no unverified "yes" claims, consistent with the compliance rule that unverified means "not yet."

### 3. Consistency with my own T-21-1 drafts and `vendor-inventory.md`

- `legal/privacy.md:77-79` and `legal/dpa.md:100-101` cite the identical figures and the identical file:line (`orders/jobs.ts:13` `PII_RETENTION_DAYS = 30`, `privacy/service.ts:285` `BUYER_PII_RETENTION_MONTHS = 18`) as `v1-review.md`'s DPP table. No drift between the two documents.
- `legal/dpa.md:61` defers the MFA claim to `v1-review.md`/the DPP evidence pack rather than asserting it — consistent with this commit leaving MFA open.
- The DPP table's "Third-party risk assessments" row correctly points to T-21-1's `vendor-inventory.md` (same wave), which I own and which exists with the same "not yet" honesty (every `[[OWNER: ...]]` cell for access owner/rotation is a real gap, not an invented "yes").
- No conflicting retention, breach-notice or sub-processor figures found between the two cards' output.

### 4. Verification command and counts

- `grep -n "180" invai-docs/security -r` → no output (re-ran myself; exit 1). AC1 satisfied.
- Findings-table recount (37 rows, S-01..S-37) against the stated "6 High (all fixed) / 16 Medium (15 fixed, 1 mitigated) / 15 Low (8 fixed, 1 closed, 2 partially fixed, 4 open)": recounted by severity and status myself — the arithmetic is exact (High: S-01,02,03,04,35,36=6; Medium: S-05..19,33=16, mitigated S-14 only; Low: S-20..32,34,37=15, fixed 8 = S-20,21,22,23,24,27,28,31, closed 1 = S-34, partial 2 = S-30,S-37, open 4 = S-25,26,29,32). No miscount.

## The 4 DPP items with no backlog id

All four are real DPP requirements, confirmed against the live Amazon pages above, and none exists in code today (confirmed by grep, read-only, `respect-ownership`):
1. Account lockout distinct from IP rate limiting — real gap.
2. Password history (last 10) — real gap.
3. 18-month non-PII retention sweep (separate from the existing 18-month buyer-PII redaction) — real gap.
4. Mandatory MFA for owner/admin — real gap (plugin present, not enforced).

Agree with the author: these need backlog ids before the SP-API restricted-role application. Since backlog ownership is the PM's and routing is the tech lead's (`respect-ownership`), I'm not adding rows myself. Flagging to the tech lead to route to product-manager, same as the author's report already requests — this review adds no new escalation, just confirms the request is warranted.

## Other observations (non-blocking)

- The card's own instruction to leave the CI section as "planned: wave 11 prep" was followed, but the author additionally named the real scheduled backlog rows (B-08, B-21) and card (T-25-1). This is more useful than a bare placeholder and doesn't overstate anything as done — no objection.
- `vulnerability-management.md`'s Medium (90-day) SLA is explicitly labeled InvAI's own policy, not Amazon's — correct; Amazon states no SLA for Medium/Low per the fetched page.
- Owned paths: `git -C invai-docs diff --stat` for this commit touches only `security/v1-review.md`, `security/vulnerability-management.md`, `waves/21/reports/T-21-3.md` — all inside the card's owned paths (`invai-docs/security/**`).

## Gaps

None found in this card's own scope. The four DPP items above remain unrouted to the backlog (owner: tech lead → product-manager), consistent with the author's report.
