# Review of T-7-4 (round 2)

- Reviewer: qa-engineer on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-docs/waves/7/wave.md:149` | grant recorded, covers `integrations/channels/**` (hold signals, Walmart line-cancel) and `db/schema/orders.ts` + migration 0022, matching round 1's flagged paths exactly |
| `git -C invai-backend log --oneline 16ddc52..0e16314` | unchanged, no new commits — confirms "no code changes" as stated |

Round 1's test-coverage and golden-path evidence stands: tsc/biome clean, vitest 79 files/567 tests passed, `scan-test-weakening.sh` no hits, all six acceptance criteria covered by tests I independently traced (USPS holiday dates hand-verified, staleness watermark scenario tested, per-line cancel/hold cases enumerated), and golden-path E2E specs never hardcode a ship-by date so the wave gate isn't at risk. None of that re-runs differently since nothing in the diff changed between rounds — see `T-7-4-qa-engineer-r1.md` for the full evidence table.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1-6 | Yes | Unchanged from round 1. |

## Blocking findings
None. Round 1's finding was purely the missing `wave.md` record for the `integrations/channels/**`/`db/schema/orders.ts` grant; the tech lead has confirmed the grant was given in the build prompt and it's now recorded at `wave.md:149`. No test or code changes accompanied this, so there's nothing new to re-verify functionally.

## Checks
- [x] Only owned paths changed, now including the documented grant
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (unchanged from round 1)
- [x] Tenancy, idempotency, money in cents, en/es text (unchanged from round 1)
- [x] Decisions recorded where needed — grant and staleness design both on record

## Optional notes (not blocking)
Carried over from round 1: `db/seed/builder.ts`'s ship-by generation still bypasses `computeShipBy` (pre-existing, out of this card's scope) and the `import-edits.test.ts` case count in the original report is stale (11 cases now, not 10) — neither affects this verdict.
