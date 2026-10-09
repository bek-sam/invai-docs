# Review of T-29-4 (round 2)

- Reviewer: reviewer on Opus 5.5. Author: backend-engineer on Opus 5.5. Commit reviewed: invai-backend 2872c59.
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat 2872c59` | 1 file: `src/modules/channels/webhook-auto-import.test.ts` (+84/-5); no product code |
| `pnpm vitest run src/modules/channels --reporter=dot` (shared tree, clean) | 9 files, 59 passed |
| Mutant `if (!known)` -> `if (true)` in sync.ts:909, scratch `git archive 2872c59` copy (removed) | 2 failed / 5 passed: update test "expected null to be 'please gift wrap'"; Etsy cancel "expected 'needs_attention' to be 'cancelled'" |
| `scan-test-weakening.sh invai-backend 384ef6f` | only hit: old `toHaveLength(1)` line, re-added as `expect(rows).toHaveLength(1)` plus note and `channelUpdatedAt` asserts (stronger) |

## Round 1 finding 1: fixed
- Update test now flips auto-import off (line 163) after the create, then asserts `buyerNote` and `channelUpdatedAt` 10-02 changed.
- New Etsy `ORDER_CANCELED` (order_ref) test on a known order with auto-import off asserts `cancelled`. Both go red under always-skip.

## Acceptance criteria
1, 3, 4, 5: unchanged since r1 (met). 2: now met with proof (mutant above).

## Checks
- [x] Owned path only; tests only; nothing loosened, no `.skip`/`.only`; the shared dev DB was not touched.
