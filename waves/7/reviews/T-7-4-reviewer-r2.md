# Review of T-7-4 (round 2)

- Reviewer: reviewer on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "Grant (tech lead" invai-docs/waves/7/wave.md` | `wave.md:149` — "Grant (tech lead, 2026-09-26), recorded here: T-7-4 was granted `integrations/channels/**` for the hold signals ... and the Walmart CSV per-line cancel fix, plus `db/schema/orders.ts` `channel_updated_at` with migration 0022 and about 3 lines in `sync.ts`." Matches exactly the paths flagged in round 1 (`csv/parse.ts`, `types.ts`, `orders.ts`, migration 0022). |
| `git -C invai-backend log --oneline 16ddc52..0e16314` (re-checked, no new commits) | still `6caf8db`, `0e16314` only — no code changes since round 1 |

Round 1's only blocking finding was the missing `wave.md` record for this grant, not the code itself — round 1's re-run evidence (tsc/biome/vitest clean, scan-test-weakening no hits, all six acceptance criteria met, USPS holidays/ship-by math/staleness column/per-line-cancel/holds all verified) stands unchanged; see `T-7-4-reviewer-r1.md` for that evidence, not re-run here since nothing in the diff moved.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1-6 | Yes | Unchanged from round 1 (`T-7-4-reviewer-r1.md`); no code changed between rounds. |

## Blocking findings
None. Round 1's finding (ownership grant for `integrations/channels/**` and `db/schema/orders.ts` undocumented in `wave.md`) is resolved: the tech lead confirmed the grant was given in the build prompt and it is now recorded at `wave.md:149`.

## Checks
- [x] Only owned paths changed (now including the granted paths, recorded in `wave.md:149`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (unchanged from round 1)
- [x] Tenancy, idempotency, money in cents, en/es text (unchanged from round 1)
- [x] Decisions recorded where needed — staleness design (`wave.md:148`) and the ownership grant (`wave.md:149`) are both now on record

## Optional notes (not blocking)
Carried over from round 1, still true: `holdFromChannel`'s two new hold notes are English-only user-facing text; worth a follow-up if surfaced untranslated in the UI. Not a blocker.
