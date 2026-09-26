# Review of T-7-1 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: integrations-engineer + web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend` worktree @`12dcb40`: `node_modules/.bin/tsc --noEmit` | clean |
| same: `node_modules/.bin/biome check .` | Checked 46 files, no issues |
| same: `vitest run src/modules/shipping/export-tracking.test.ts src/integrations/channels/exports/tracking.test.ts` ×3 | 14/14 pass every time (previously failed 1/14 deterministically in r1) |
| same: full `vitest run` (own test DB `invai_test_review71r2`) | 567/567 pass |
| `invai-web` worktree @`a915bdd`: `tsc --noEmit`, `biome check .`, `vite build`, `vitest run` | build/tests pass (76/76). `tsc` shows 8 pre-existing errors (`is-own-demo.test.ts`, `index.tsx`, `drafts.$draftId.tsx` — `acknowledgeRisk`) — confirmed present on the parent commit `f41f60b` too (checked out that tree and re-ran `tsc`), i.e. from another card's in-flight work, not from `a915bdd`'s one-file i18n diff. Out of scope for T-7-1. |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits belong to other cards' commits already on `main`; T-7-1's own r2 diff (`export-tracking.test.ts`) only adds assertions (a 3x loop replacing a single `expect`), removes none |
| Read `service.ts`'s new predicate in full: `conds.push(since ? gte(shipments.labeledAt, since) : isNull(shipments.exportedAt))` | confirmed |
| Cleanup | dropped `invai_test_review71r2`, removed both worktrees |

## AC2 check (explicit ask from the tech lead): does an explicit date-range re-export still include already-exported shipments?
Yes — verified two ways:
1. **Code**: when `since` is provided, the `isNull(shipments.exportedAt)` condition is not added at all; the only filter is `gte(shipments.labeledAt, since)` (plus the unrelated labeled/tracked/not-voided/not-pushing conditions and the optional `until`). Nothing in that branch looks at `exportedAt`, so a shipment already marked `exportedAt` matches exactly the same as one that isn't, as long as its `labeledAt` falls in range.
2. **Test**: `export-tracking.test.ts`'s existing "replay" case — export once (`since:null`, count 1, shipment now has `exportedAt` set), confirm three back-to-back `since:null` calls all return 0, then call with an explicit `since` from 60s in the past and get `count:1` again, re-including the same already-exported shipment. Ran this file 3× in isolation, passed every time.

The date-range re-export path was not lost.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Export files per CSV channel, own format, carrier mapping | Yes (unchanged from r1, already approved) | |
| 2. `exported_at` marks shipments; re-export possible (default = idempotent, explicit range = re-includes) | **Yes** | See above; r1's blocking finding is fixed at the root (no more cross-clock comparison at all for the default path) rather than papered over |
| 3. Web button, count, download, en/es hint | **Yes** | `a915bdd` translates the two remaining raw-English hints; all four `exportWhere` strings now differ between `en.ts` and `es.ts` (diffed both files side by side) |
| 4. Fixtures for each format | Yes (unchanged) | |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`service.ts`, `export-tracking.test.ts`, `es.ts`).
- [x] Nothing outside scope.
- [x] Tests exercise the behavior; none weakened — the r2 diff only adds assertions.
- [x] Tenancy unchanged from r1 (already fine).
- [x] Idempotency: fixed — the default path no longer depends on comparing two independently-sourced clocks; `exportedAt IS NULL` is a boolean the export itself sets on the exact row it reads, so it can't self-contradict.
- [x] Money in cents: n/a.
- [x] en/es text: both raw-English strings translated; menu-path literals (Seller Central, Seller Center, etc.) intentionally kept as English UI labels, consistent with the existing Etsy/Walmart convention — reasonable.

## Optional notes (not blocking)
- The unrelated `tsc` errors in `invai-web` (AI-listings `acknowledgeRisk`, demo-mode test) predate this card's commits and aren't caused by it; flagging for the tech lead to route to whichever card owns `drafts.$draftId.tsx` / `is-own-demo.test.ts` / `index.tsx`.
- Pluralization nit from r1 ("1 shipments exported") is still present; still not blocking.
