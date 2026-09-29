# Wave 21: evidence and docs (wave 14, part 2): policies, legal drafts, help center, runbook

- Dates: planned 2026-09-28, starts when wave 20's builders free slots
- Goal (user outcome): a shop owner signing up sees links to the terms and privacy policy and a Help link that opens real articles in English and Spanish; the owner has lawyer-ready drafts (terms, privacy, DPA, sub-processors) and the written security and incident policies Amazon, Shopify and pilots ask for; a new engineer sets up and resets the stack from the runbook without surprises.
- Sources: backlog B-10, B-29, B-98, B-106 (docs part), plus runbook lines from T-20-5 and the wave 19 gate (stale jobs after reset). Scope: `always-in-scope: compliance` (B-10, B-29), `product/scope.md#mvp-in` item 14 (onboarding; B-98), `always-in-scope: bug` (B-106 runbook).
- Rules: `team/agent-brief.md`. Every prompt: "Don't push; only the tech lead pushes after the gate", absolute memory path, record PIDs.
- Fences: nothing is published or sent. Legal text is a **draft for counsel** (owner track); every legal page in the app carries "Draft, pending legal review" until the owner records counsel's sign-off. No claim of "secure", "compliant" or "guaranteed" in shop-facing text without compliance-officer review.
- Plan reviewed by: product-manager (2026-09-28, approve), architect (2026-09-28, T-21-5 approve with change A1: content drift check).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-21-1 Legal drafts for counsel: terms, privacy policy, DPA, sub-processor list, vendor inventory (B-10 part) | compliance-officer | sonnet | product-manager (domain) + security-reviewer (data flows) | pii, marketplace-policy | planned |
| T-21-2 Incident-response plan and access-control policy (B-10 part) | platform-sre | sonnet | reviewer (opus) + security-reviewer | security | planned |
| T-21-3 Security docs corrected: Amazon 30-day scans, DPP 2025-11, vulnerability SLA (B-29) | security-reviewer | sonnet | reviewer (opus) + compliance-officer | security | planned |
| T-21-4 Help center en/es and runbook fixes (B-98 content, B-106 docs) | docs-writer | sonnet | product-designer (domain, plain language) + compliance-officer (claims) | ui (copy) | planned |
| T-21-5 In-app Help and legal links (B-98 web half) | web-engineer | sonnet | reviewer (opus) + product-designer | ui | planned |

## Order and ownership
1. T-21-1, T-21-2, T-21-3 in parallel (docs only; 3 agents).
2. T-21-4 when a slot frees; T-21-5 last (it bundles T-21-1's and T-21-4's text).

| Card | Owns (exclusive) |
|---|---|
| T-21-1 | `invai-docs/legal/**` (new: `terms.md`, `privacy.md`, `dpa.md`, `subprocessors.md`, each en and es), `invai-docs/compliance/vendor-inventory.md` |
| T-21-2 | `invai-docs/ops/incident-response.md`, `invai-docs/ops/access-control.md`, `invai-docs/ops/README.md` |
| T-21-3 | `invai-docs/security/**` |
| T-21-4 | `invai-docs/help/{en,es}/**`, `invai-docs/build/runbook.md`, `invai-docs/build/demo-guide.md` (only if a step is wrong) |
| T-21-5 | `invai-web/src/routes/signup.tsx` (links only), new `invai-web/src/routes/help/**`, new `invai-web/src/routes/legal/**`, new `invai-web/src/content/**` (bundled copies), new `invai-web/scripts/sync-content.*`, the app-shell Help entry (file named in the report), `src/i18n/en.ts` + `es.ts` (its keys) |

## Build log
- 2026-09-28 T-21-1 `3cffec0` + r2 `30b1506`: security r1 approve, PM r2 approve. **Approved.** OI-19 (counsel timing) filed.
- 2026-09-28 T-21-2 `b2d3565`/`fa7e6cd` + r2 `9d5ac3e`: reviewer r2 approve, security r2 approve. **Approved.** Found B-189 (guard does not block `sst secret set` or branch-protection API calls).
- 2026-09-28 T-21-3 `ed0ef87` + r2 `6fc90a2`: reviewer r2 approve, compliance r1 approve. **Approved.** DPP gaps filed as B-185..B-188.
- 2026-09-28 T-21-4 building (docs-writer). T-21-5 waits on T-21-4 and the architect's plan review.
- Night rule (coordinator, 2026-09-28): owner asleep; apply each OI's safe default; don't stall on two failed rounds (record and move on).

## Integration gate
- [ ] Fresh reset, migrate, seed; `run-golden-path` (sign-up and the app shell are touched)
- [ ] Help and legal pages looked at in en and es at 390 and 1440 px
- [ ] Owner-inbox entry for counsel review of the drafts exists
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Retro
