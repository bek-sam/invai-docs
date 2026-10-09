# Review of T-29-5 (round 1)

- Reviewer: reviewer on Opus 5.5. Author: architect on sonnet.
- Diff: `invai-contracts` dc62328..0f666f1 (1 commit, 6 files, +45/-3).
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| contracts `pnpm typecheck && pnpm lint && pnpm test` | exit 0; biome 64 files clean; 12 files, 147 tests pass |
| invai-web `pnpm typecheck` | exit 0, clean |
| invai-floor `pnpm typecheck` | exit 0, clean |
| new test vs base (git archive dc62328 + new `schemas.test.ts`) | FAILS on base (1 failed / 12 passed): test proves the change |
| `scan-test-weakening.sh invai-contracts dc62328` | no hits (removed=0 added=3) |
| grep web/floor src for `ITEM_ARTWORK_STATUSES`, `artworkStatus`, artwork `.status` | no exhaustive switch or typed `Record<status,…>`; see notes |
| backend typecheck | not judged (T-29-1 working tree in flight, per tech lead) |

## Acceptance criteria
1. Met. `purged` appended last in `ITEM_ARTWORK_STATUSES` (schemas/personalization.ts:126) and `ItemArtworkSummary.status` (orders.ts:83); old five values keep order; all 7 summary statuses parse (schemas.test.ts:309).
2. Met. Report lists the `counts` record break (contract/personalization.ts:62, `z.record(z.enum(...))`) and backend errors at router.ts:30 tracing to service.ts ~:723/:790, owned by T-29-1; web and floor clean (re-run above).
3. Met. Doc comment on the enum (schemas/personalization.ts:121-125) states the meaning and "re-enter to print".

## Blocking findings
none

## Checks
- [x] Only owned paths changed: schemas/personalization.ts, schemas/orders.ts, compat.ts, package.json, schemas.test.ts, CHANGELOG.md
- [x] Nothing outside scope; additive only (nothing removed or renamed). Version 0.14.0 in package.json and `CONTRACT_VERSION` (held equal by compat.test.ts:13); floor baseline 0.3.0 unchanged
- [x] Test exercises the behavior and fails without the change; none weakened
- [x] Tenancy / idempotency / money / en-es: n/a (contract enum only; no strings in contracts)
- [x] Decisions: none needed (additive minor bump per the 0.x rule)

## Optional notes (not blocking)
- Web shows raw `purged` until T-29-3 adds the label: `t(\`artworkStatus.${status}\`, status)` at order-detail.tsx:347 and personalization.index.tsx:144/:217 fall back to the value; `invai-web/src/i18n/en.ts:173` has no `purged` key. The status filter dropdown will list `purged` automatically (it maps `ITEM_ARTWORK_STATUSES`); `counts[s] ?? 0` is safe. T-29-3 must add en/es `artworkStatus.purged`.
- The list input `status` filter (contract/personalization.ts:54) now accepts `purged`; T-29-1 must widen the service filter type too (the TS2345 the report names).
