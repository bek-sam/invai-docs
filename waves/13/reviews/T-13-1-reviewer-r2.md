# Review of T-13-1 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: architect + floor-engineer + backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 9453eb1` | `FLOOR_COMPAT_BASELINE = "0.3.0"` added to `src/compat.ts`, independent of `CONTRACT_VERSION`; CHANGELOG line added; new test asserts it's a real, parseable version `<= CONTRACT_VERSION` |
| `git -C invai-backend show 969103a` | `env.ts`'s `MIN_FLOOR_CONTRACT_VERSION` default changed from `CONTRACT_VERSION` to `FLOOR_COMPAT_BASELINE`; new test mocks `@invai/contracts` to `CONTRACT_VERSION: "9.9.0"` (simulating an unrelated bump) via `vi.doMock` + `vi.resetModules`, re-imports `env` and `orpc`, and asserts a tablet on today's version still passes both `floor` and `station` checks |
| `git -C invai-docs show eef2193` | ADR 0012 §2, §5, §6 and Consequences rewritten to describe `FLOOR_COMPAT_BASELINE` as the default and the env var as an emergency-only override; the r1 "every bump forces update" consequence is removed and replaced with the correct one |
| `pnpm --dir invai-contracts vitest run src/compat.test.ts` (`perl -e 'alarm 120; exec @ARGV'`) | 5/5 passed (was 4/5 pre-fix) |
| `pnpm --dir invai-backend vitest run src/api/contract-version.test.ts src/api/email-gate.test.ts` | 13/13 passed (was 11/11 pre-fix) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts origin/main` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits present, all traced to T-12-1/T-12-4 code (`jobs.ts`, `sweeps.ts`, retry-backoff tests), none in `contract-version.test.ts` or `env.ts` — the `vi.doMock("@invai/contracts", ...)` in the new test mocks a dependency to simulate a version bump, not the unit under test, and is unmocked/reset in a `finally` |

## Blocking findings from r1 — resolved
1. **`MIN_FLOOR_CONTRACT_VERSION` default tied to `CONTRACT_VERSION`** — fixed exactly as prescribed: `FLOOR_COMPAT_BASELINE` is a separate, hand-bumped constant in `invai-contracts/src/compat.ts`; `env.ts` defaults to it; a new test proves a contracts-version bump alone (mocked to `9.9.0`) no longer refuses a tablet still on the real current version, on both `floor` and `station` modes. ADR 0012 now matches the mechanism. No remaining gap: the 14-day grace-window guarantee no longer depends on an env var surviving every intervening redeploy.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 4. Documented compatibility policy | Yes, now fully | ADR 0012 §5/§6 correctly describe `FLOOR_COMPAT_BASELINE` as the thing that holds across the window; env var demoted to an emergency lever, matching what the code actually does |
| 1, 2, 3, 5 | Unchanged from r1 (approve) | no code touched outside the fix; re-ran and still green |

## Checks
- [x] Only owned paths changed (`compat.ts`, `compat.test.ts`, `CHANGELOG.md` in contracts; `env.ts`, `contract-version.test.ts` in backend; ADR 0012 + report in docs — all T-13-1's)
- [x] Nothing outside scope
- [x] Tests exercise the fix directly (mocked-version test), and none were weakened
- [x] Decisions recorded — ADR 0012 corrected

## Optional notes (not blocking)
- The new backend test's `vi.doMock`/`vi.resetModules`/dynamic `import()` dance is a bit heavy for what it proves; a simpler version would pass `CONTRACT_VERSION` as an explicit parameter the way `enforceFloorContractVersion`'s third arg already does elsewhere in the file. Not worth a third round over.
