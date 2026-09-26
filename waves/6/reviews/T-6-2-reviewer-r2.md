# Review of T-6-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **approve**

Round 1's blocking finding: `markSheetPrinted` had no guard, so a vendor-path sheet could be
forced straight to `printed` via `production.sheets.markPrinted`, bypassing the vendor
confirmation entirely. Fix: `invai-backend` `5798498`.

## Evidence I re-ran
Worktree pinned to `5798498` (detached HEAD), its own `node_modules` (per-entry symlinks,
`@invai/contracts` pointed at the live `invai-contracts` — no wave-6/7 stub-ordering issue this
time, contracts is well past that point). Removed at the end.

| Command | Result |
|---|---|
| `tsc --noEmit` | pass |
| `biome check .` | pass, no fixes |
| `vitest run src/modules/production` (own DB `invai_test_t62r2`) | 5 files, 38 tests passed |
| `vitest run` (full suite) | 542/543 passed — 1 failure, in `src/modules/shipping/export-tracking.test.ts` (a T-7-1 area, untouched by this card's diff; unrelated to this fix, not chased further) |
| Read `git show 5798498 -- src/modules/production/sheets.ts` and `print-bins.test.ts` in full | see below |
| **Critical check — live, on a fresh DB copy** (`invai_t62r2_copy`, API :3196, imaging :8194, `REDIS_URL` db 12): signed in as `owner@desertbloom.test`, found sheet `#25` (vendor "Sun City DTF") back at `sent`; signed in as `vendor@suncitydtf.test`, called `POST /vendor-portal/sheets/71923822-3bdd-4b3b-8110-7f9ab3bb5454/printed` | **succeeded** — sheet moved `sent → printed`, `printedAt` stamped. The vendor's own "Mark printed" flow is unaffected by the fix. |

**Aside — infra, not code:** partway through this round OrbStack's Docker daemon dropped (its
socket disappeared: `dial unix .../docker.sock: connect: no such file or directory`), which is
why the API hung with no output for several minutes against a copy DB that briefly couldn't be
reached. The tech lead restarted it; Postgres data survived (my copy/test DBs were still there),
Redis was empty, so I killed and restarted every process I'd started against the stale connections
before running the checks above. Unrelated to this card.

## The fix, and why it's sufficient
```ts
if (sheet.status !== "printing" || !(await companyPrintsInHouse(tx, ctx.companyId)))
  throw invalidTransition("sheet", sheet.id, sheet.status, "printed");
```
This closes exactly the gap from round 1: `markSheetPrinted` now refuses unless the sheet is
already `printing` (which only `markSheetPrinting` can reach, itself gated on `printsInHouse`)
**and** the company still prints in-house. A vendor-flow sheet is never `printing`, so it can never
satisfy this check — confirmed live in round 1 that a `sent` sheet was rejected before the fix
succeeded, and now `print-bins.test.ts`'s two new cases assert `INVALID_TRANSITION` for exactly
that (a `sent` sheet with `printsInHouse` false, and an `acknowledged` sheet even with
`printsInHouse` true).

## Critical item: does this break the vendor portal's own "Mark printed"?
No. Traced the full call chain:
- `invai-web`'s vendor route (`src/routes/_app/vendor/sheets.$sheetId.tsx:133`) calls
  `orpc.vendorPortal.markPrinted`, **not** `orpc.production.sheets.markPrinted`. These are
  different contract routers (`vendorPortal` vs `production.sheets`) on different permission
  scopes (`vendor_portal.update` vs `production.build`).
- `invai-backend`'s `vendorPortalRouter.markPrinted` (`src/modules/vendors/router.ts:41`) calls
  `svc.vendorUpdate(tenant, id, { kind: "printed" })`.
- `vendorUpdate`'s `"printed"` case (`src/modules/vendors/service.ts:596`) calls
  `transitionSheet(tx, shopId, actor, sheet, "printed")` **directly** — it never touches
  `markSheetPrinted` or `companyPrintsInHouse` at all.
- Neither `5798498` nor T-6-2's original commits touch `src/modules/vendors/*` or
  `invai-web`'s vendor routes (confirmed: `git diff` on both commits against those paths is empty).

Confirmed live above: the vendor's `printed` transition still works after the fix. Golden-path
step 6 is safe.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. In-house printing, vendor path unchanged | **yes** | Round 1's exploit now refused (`INVALID_TRANSITION`, confirmed by the two new tests); the happy path (round 1's own live pass) is untouched by this commit; the vendor's own path to `printed`, verified live again this round, is unaffected. |
| 2–4 | unchanged from round 1 | Not re-verified this round — this fix touches only `markSheetPrinted`'s guard; nothing else in the card changed. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed: `src/modules/production/sheets.ts` (the guard) and
  `src/modules/production/print-bins.test.ts` (two new tests) — both inside this card's owned
  `modules/production/**`.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, none weakened: both new tests assert `INVALID_TRANSITION` and,
  for the `sent` case, also assert the row's `status`/`printedAt` are untouched — real proof, not
  a relaxed check. `scan-test-weakening.sh invai-backend-t62-r2 5798498~1` (run as part of the
  commands above): no hits.
- [x] State-machine safety: now holds — see above.
- [x] Decisions: the fix's own commit message correctly explains why the vendor path needed no
  change; no new decision doc needed for a bug fix.

## Optional notes (not blocking)
- The one full-suite failure (`export-tracking.test.ts`, T-7-1's shipping-export area) is unrelated
  to this card's files; flagging for whoever owns that area, not blocking this review.
