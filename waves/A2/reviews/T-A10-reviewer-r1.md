# Review: T-A10 A2 contract 0.10.0, round 1
Reviewer: reviewer (opus). Author: architect (opus). Diffs: invai-contracts 6349ddf, invai-backend 3ebfbf8. Date: 2026-09-30.
**Verdict: approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| invai-contracts `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 60 files, no fixes; vitest 10 files / 121 tests passed |
| invai-floor `pnpm typecheck` | exit 0 |
| invai-backend `pnpm typecheck` (read-only, no tests) | 2 errors, only `digest/build.ts:315`, `digest/rank.ts:14` (accepted, T-A9); `today/router.ts` stub compiles |
| invai-web `pnpm typecheck` | 1 error, only `components/digest/digest-copy.ts:106` (accepted, T-A7/T-A6 per ruling 5) |
| `scan-test-weakening.sh invai-contracts 6349ddf~1` | hits = the two changed tests below; no skip/only, config or snapshot changes |

## Acceptance criteria
1. Additive only: **met**. Diff removes nothing: detectors D9..D13 appended after `market`, six kinds appended after `none` (ruling 1 names, D11 split), `DigestActionParams` gains only optional `style/color/size/supplierId/supplierName/points/deltaCents` (no buyer fields), new schemas/procedures only. Consumers: no errors beyond the accepted three (floor clean).
2. Tests: **met**. `today-actions.test.ts` pins detector tail + old 9-prefix, six kinds, params (int `deltaCents`, uuid `supplierId`), `finance.read` on both, `auth` user, GET `/today/actions` / POST `/today/actions/clicks`, finance.read holders = owner/admin/office, `ACTION_NOT_FOUND` 404, max 5 + rank 1..5, `impactCents` int or null, `key` required 1..128, href rule, `generatedAt` null.
3. Version 0.10.0: **met** (`package.json`, `compat.ts`, CHANGELOG; exact pin in `today-actions.test.ts:199-201`).
4. Stub: **met by code** (`stubRouter` throws `notImplemented(name)`, `api/orpc.ts:199-209`); not called live, per instruction to start no servers.

## Rulings 1-3
`recordActionClick` name/route, six kinds, `TodayAction = DigestAction.extend(...)`, `auth` default user (`_base.ts` doc) and tested, `generatedAt` nullable, `ACTION_NOT_FOUND`, `shipmentsWithoutZone` text-only fix: all present.

## Changed old tests (not weakened)
- `analytics.test.ts` version: exact pin moved to the newest test (0.10.0) with floor baseline still pinned; the relaxed `>= 0.9.0` is the agreed "newest wave pins" pattern.
- `digest.test.ts`: D9 is now valid by design; the unknown-detector negative check is kept with D14.

## Checklist
Tenancy/idempotency/migrations: n/a (contract only; T-A9 owns tables). Money: `impactCents`/`deltaCents` integer `Cents`. No PII in params. Zod on all inputs. Floor invariants untouched; `FLOOR_COMPAT_BASELINE` unchanged. Ownership: contracts `src/**`, package.json, CHANGELOG, backend `today/router.ts` only.

## Blocking findings
none

## Optional notes (non-blocking)
- The kinds test pins old order only via `indexOf("none") === 10`; the existing digest tests cover the old names.
