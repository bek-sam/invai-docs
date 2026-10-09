# Review of T-28-1 (round 1)

- Reviewer: reviewer on opus (claude-opus-5-5)
- Author: architect on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts log origin/main..HEAD` / `show --stat dc62328` | one commit, 8 files: CHANGELOG, README, package.json, compat.ts, _base.ts, photos.test.ts, schemas.test.ts, schemas/tenancy.ts; tree clean |
| contracts `pnpm typecheck && pnpm lint && pnpm test` | exit 0; biome 64 files clean; 12 files, 146 tests pass |
| invai-web `pnpm typecheck` (symlinked to contracts, web tree clean) | exit 0 |
| invai-floor `pnpm typecheck` (also links contracts) | exit 0 |
| invai-backend `pnpm typecheck` (dirty tree: T-28-2/T-28-3 uncommitted work) | exit 0 |
| `scan-test-weakening.sh invai-contracts origin/main` | 1 removed assertion (exact `0.12.0` pin, card-mandated relax to `isContractVersionAtLeast(…,"0.12.0")`); version sync still held by `compat.test.ts:12-13` (`CONTRACT_VERSION === pkg.version`) |
| `grep -e 0.12.0 -e 0.13.0` in backend/web/floor src | no consumer pins the contract version (only comments in backend `db/schema/ai.ts`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `_base.ts:70-74` `MFA_REQUIRED` 403, `data: z.object({ deadline: Timestamp.nullable() })`; test checks null, ISO and rejects "soon"; backend+web typecheck with it |
| 2 | yes | `tenancy.ts:102-104` `.optional()`; test parses undefined, full object, and rejects a missing `deadline` |
| 3 | yes | `index.ts:27` `export * from "./schemas/tenancy"`; test imports both from `./index` and checks literal order and the `code` literal |
| 4 | yes | diff is additions only in `src/` apart from the pin relax; 0.12.0 → 0.13.0 in package.json and compat.ts; README procedure count unchanged (no procedure added) |
| 5 | yes | `schemas.test.ts` "account security contract (T-28-1)" (3 tests) + `compat.test.ts` version sync |

Matches waves/28/wave.md "Agreed interfaces" exactly (status, data shape, `Me.mfa` fields, the three codes with 423/400/403, `retryAfterSec` int). Doc comments name T-28-2, the DPP and the "required" rule incl. vendors and sample workspaces.

## Blocking findings
none

## Checks
- [x] Only owned paths changed (all 8 paths are on the card; `schemas.test.ts` is the schema test for these files)
- [x] Nothing outside scope (no backend/web code, no other error code)
- [x] Tests exercise the behavior, none weakened (pin relax is the card's instruction; version sync still tested)
- [x] Tenancy/idempotency/money/en-es: n/a for a contract-only change; additive contract (invariant held)
- [x] Decisions recorded where needed (ADR 0025 is T-28-2's; FLOOR_COMPAT_BASELINE 0.3.0 unchanged, correct since no floor-facing shape changed)

## Optional notes (not blocking)
- `AccountLockedBody.retryAfterSec` has no `.nonnegative()`; the producer (T-28-2) should never send a negative, a `min(0)` would document that.
- CHANGELOG jumps 0.10.0 → 0.13.0 (0.11/0.12 entries were never written); pre-existing gap.
- Adding to `COMMON_ERRORS` puts `MFA_REQUIRED` on every procedure's error map; T-28-4 must keep it out of the generic toast path (the card already says so).
