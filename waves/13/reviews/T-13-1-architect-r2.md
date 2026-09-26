# Review of T-13-1 (round 2)

- Reviewer: architect (co-review) on Sonnet 5
- Author: architect + floor-engineer + backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 9453eb1 -- src/compat.ts` | `FLOOR_COMPAT_BASELINE` doc comment states the intended lifecycle correctly: hand-raised only when a floor-facing breaking change's 14-day window closes, with a CHANGELOG line, never tied to `CONTRACT_VERSION` |
| `git -C invai-backend show 969103a -- src/env.ts` | default source changed to `FLOOR_COMPAT_BASELINE`; comment updated to call the env var "the emergency/rollback override" rather than the thing carrying the grace period |
| `git -C invai-docs show eef2193 -- decisions/0012-floor-contract-compat.md` | §5's breaking-change bullet now reads "this holds across every deploy in the window with no env var to carry" — this is the exact property r1 found missing |
| `pnpm --dir invai-backend vitest run src/api/contract-version.test.ts` (`perl -e 'alarm 120; exec @ARGV'`) | 13/13 passed, including the mocked-`9.9.0` case for both `floor` and `station` modes |
| Re-read `wave.md`'s T-13-3 sequencing note | T-13-3 bumps `package.json`/`CHANGELOG.md` next; under the fixed design that bump alone does not move `FLOOR_COMPAT_BASELINE`, so it will not force floor tablets to update — confirms the fix actually closes the scenario I flagged in r1 (a same-wave, non-floor-facing bump) |

## r1 finding — resolved
The design gap I raised (minimum's default conflated "current build" with "oldest still-compatible") is fixed at the root: `FLOOR_COMPAT_BASELINE` is now a distinct, hand-maintained value that only a deliberate contracts commit can move, and it lives in the same file/package as `CONTRACT_VERSION` so it's reviewable in the same diff as any future floor-facing breaking change. The env var is no longer load-bearing for the grace-period guarantee — it's correctly scoped down to "ops emergency lever" in both the code comment and ADR 0012 §6. I'm satisfied this generalizes correctly to T-13-3's upcoming bump and to future waves.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 4. Documented compatibility policy | Yes | ADR 0012 now accurately describes the mechanism; no remaining mismatch between promise and implementation |

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope; no collision with T-13-3/T-13-2's `package.json`/`CHANGELOG.md` sequencing
- [x] Tests exercise the fix directly, none weakened
- [x] Decisions recorded correctly

## Optional notes (not blocking)
- Worth a one-line addition to `runbook.md` (already tracked as B-106) clarifying that `MIN_FLOOR_CONTRACT_VERSION` is now an override of `FLOOR_COMPAT_BASELINE`, not of `CONTRACT_VERSION` — so ops doesn't go looking in the wrong place when B-106 gets picked up.
