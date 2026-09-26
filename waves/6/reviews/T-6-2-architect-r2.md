# Review of T-6-2 (round 2) — architect co-review (printing state)

- Reviewer: architect on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **approve**

Round 1 finding: `markSheetPrinted` had no `printsInHouse`/state guard, so a vendor-path sheet
(`sent`/`acknowledged`) could be forced straight to `printed` through it, since `SHEET_TRANSITIONS`
alone allows `sent`/`acknowledged → printed` (that's how the vendor path always reached it). Fix:
`invai-backend` `5798498`. Full command evidence is in `T-6-2-reviewer-r2.md`; this file re-checks
only the state-machine-safety question this co-review exists for, plus the vendor-portal question
the tech lead flagged as critical this round.

## 1. The fix closes the gap the transition table alone can't
```ts
if (sheet.status !== "printing" || !(await companyPrintsInHouse(tx, ctx.companyId)))
  throw invalidTransition("sheet", sheet.id, sheet.status, "printed");
```
Round 1's point stands: `SHEET_TRANSITIONS` was never wrong (`printing` is still unreachable from
a vendor state, exactly per `wave.md`). The bug was that a *procedure* could reach `printed` from
states the table allows but this specific in-house-only endpoint shouldn't accept. This check adds
exactly the missing procedure-level restriction — `markSheetPrinted` now only succeeds from the
one state its name implies (`printing`), on a company that's actually in-house. Nothing about the
transition table changed, and nothing needed to: the fix is at the right layer.

## 2. Verified live this round
On the DB copy used for `T-6-2-reviewer-r2.md`'s pass: called `production.sheets.markPrinted`
directly on the same vendor sheet (`sent`, `printsInHouse` false) that round 1 forced to `printed`
— refused. `print-bins.test.ts`'s two new cases cover this in both directions (`sent` with the
setting off, `acknowledged` with the setting *on*, since a shop can print in-house for some sheets
and still receive vendor sheets for others — the guard correctly checks the sheet's own state, not
just the company setting).

## 3. Critical this round: the vendor portal's own "Mark printed" must still work
This is the one way this fix could have gone wrong — over-tightening a shared code path instead of
just the new one. Traced it: `invai-web`'s vendor sheet route calls `orpc.vendorPortal.markPrinted`
(`src/routes/_app/vendor/sheets.$sheetId.tsx:133`), a completely different contract procedure from
`production.sheets.markPrinted` — different router (`vendorPortal` vs `production.sheets`),
different permission (`vendor_portal.update` vs `production.build`), different backend function
(`vendorUpdate`'s `"printed"` case, `src/modules/vendors/service.ts:596`, calling
`transitionSheet` directly — never `markSheetPrinted`). The fix's new guard lives entirely inside
`markSheetPrinted` and is never on this call path.

Confirmed live: signed in as `vendor@suncitydtf.test`, called
`POST /vendor-portal/sheets/{id}/printed` on the same vendor sheet — succeeded, `sent → printed`,
`printedAt` stamped, exactly as before this fix. Golden-path step 6 (the vendor prints and marks a
sheet printed) is intact.

## Checks
- [x] `printing → printed` now requires both `printsInHouse` and the sheet actually being
  `printing` — the box round 1 left unchecked.
- [x] Vendor's own `sent/acknowledged → printed` (via `vendors/service.ts`, never through
  `markSheetPrinted`) is untouched by the fix, confirmed live.
- [x] No other transition or procedure was tightened or loosened by this commit (diff is exactly
  the one guard plus its two tests).

## Blocking findings
None.

## Optional notes (not blocking)
None beyond what's already in `T-6-2-reviewer-r2.md`.
