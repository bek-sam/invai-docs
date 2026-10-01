# Backlog ranking

Owned by `product-manager`. New dated sections go on top; never rewrite an old one.

## 2026-10-01 ranking (for wave P2, slots T-P2-4 and T-P2-5)

Candidates are the P1 hand-off list (`waves/P1/wave.md` "Hand-off" item 4) plus `waves/backlog.md`.
Excluded from scoring per the tech lead's fences: anything touching `invai-backend/src/modules/catalog/**`,
`invai-web/src/routes/_app/catalog/designs.index.tsx`, `invai-web/src/components/signed-image.tsx` or
`invai-web/e2e/helpers/ui.ts` (busy on T-P2-1..3), Track D, OI-17/18 items, waves 24/25.

| Rank | Item (id, link) | Source | Pain | Shops | Conf. | Effort | Risk | Approval | Priority | Spec | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | B-223 + B-224: order-drawer timeline and Today alert bodies show raw English under the Spanish UI | `waves/backlog.md` B-223/B-224; found A1 gate screens, repeated in P1 hand-off | 3 | 3 | 4 | 2 | 1 | none | 18 | no (small i18n bug; task card from backlog row, `write-spec` not required for a one-line always-in-scope bug) | Two gate reviews (A1, P1) pinpoint the exact file:line each time; violates the plain-language en/es convention (`CLAUDE.md` Conventions) on two golden-path screens (order drawer, Today) |
| 2 | Today actions: a build that fails 3 tries keeps its `jobId`, so that day can't re-queue and the Today panel stays hidden | no B-id yet (`waves/24/wave.md` L53, `waves/A2/wave.md` T-A9 reviewer, repeated in P1 hand-off) | 4 | 3 | 3 | 2 | 1 | none | 18 | no (small; file against the Today module's idempotent-job pattern) | Flagged by T-A9's reviewer by code reading; not yet seen live in a pilot, so confidence is 3 not 5 — but the failure mode (whole daily panel disappears) is worse than a cosmetic string |
| 3 (alt) | B-230: Profit v2 "orders that lost money" shows Units 0 / Revenue $0 on every seeded losing order | `waves/backlog.md` B-230; A2 T-A6 reviews | 3 | 2 | 2 | 2 | 1 | none | 6 | no | Backend-engineer (finance) hasn't yet confirmed this is a query bug vs. reprint/cancelled orders legitimately showing zero — verify before it's definitely a fix |
| 4 (alt) | B-235: pre-v6 assistant analytics tools answer in English under Spanish UI (footer translates); separately, a full eval run exhausts the eval tenant's trial credits before `digest_narrative` | `waves/backlog.md` B-235; T-P1-3 report | 2 | 2 | 3 | 2 | 2 | none | 3 | no | Matches "Spanish-correctness" but on a legacy (pre-v6) code path with a partial mitigation already (footer translates); `ai` risk flag adds an ai-engineer co-review step; bundles in an unrelated ops-only eval-credit issue |

**Not now, needs more than a 2–3 hour single-owner slot (scored but ranked below the above by the approval/effort rule):**
- B-231 (wire imaging photo flags through the contract enum): needs the architect to shape the enum before integrations-engineer can wire it — two sequential owners, not a single small card. Pain 3, Shops 2, Conf. 4, Effort 4, Risk 1 → priority 6. Revisit once the architect has a free slot to spec the enum change.
- B-132 (assistant stream `net::ERR_ABORTED` despite a complete 200 response): root cause is inside `@orpc/client`'s event iterator (a dependency), needs an architect decision (patch vs. keep QA's allow-list), and is already mitigated by that allow-list — cosmetic log noise today, not a user-facing defect. Pain 1, Shops 2, Conf. 4, Effort 4, Risk 1 → priority 2.
- invai-ui follow-ups (PageHeader 390 px clip — a repeat on Profit and Operations, StatCard neutral, KpiTile truncation, Today top-action priority, es 4-digit money missing a group separator): owned by `product-designer` in `invai-ui`, not an engineering-repo card; bundles 5 unrelated small fixes. The es group-separator item is the strongest single piece (every Spanish shop's money display) and is worth its own small card next wave. Pain 2, Shops 3, Conf. 3, Effort 3, Risk 1 → priority 6.
- B-232 (imaging `/preview` missing from the concurrency limiter; ICC profile has no size cap): a hardening gap found in review, not an observed failure; imaging-engineer owns, not excluded by the catalog fence, but it's resource-hardening, not a user-facing bug or Spanish fix. Pain 1, Shops 2, Conf. 4, Effort 2, Risk 2 → priority 4.
- B-234 (two test flakes: `test-db.test.ts` stale sweep outside the lock, `reference/index.test.ts` tuple-concurrently-updated under load): internal gate reliability, not shop-facing. Worth doing to protect the gate from a repeat failure, but scores low on shop pain. Pain 1, Shops 1, Conf. 4, Effort 2, Risk 1 → priority 2.
- B-227 (db:reset 40P01 deadlock, seen once): excluded per the tech lead's explicit instruction — only revisit if it recurs. No recurrence recorded since the single A1 occurrence.

**Not now, out of scope:** none of the candidates are outside `scope.md`.
**Not now, waiting on approval:** none of the candidates depend on an outside marketplace/partner approval.

**Proposed wave slots:** T-P2-4 = B-223+B-224, T-P2-5 = Today actions jobId re-queue.

**What changed and why:** First ranking of the P1 hand-off candidates. Both top picks are bugs on golden-path or daily-use screens with no contract change and a single small owner, matching the tech lead's fences this wave. B-230 and B-231/B-132 need either a verification step or a second owner (architect) before they're a clean single card, so they wait. The es group-separator item inside "invai-ui follow-ups" is flagged as worth its own card next wave since it affects every Spanish-reading shop's money display, not just a cosmetic clip.
