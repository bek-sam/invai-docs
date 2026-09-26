# Review of T-6-2 (round 1) — architect co-review (printing state)

- Reviewer: architect on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **changes-required**

Scope of this co-review: the `printing` state added to `SHEET_STATES`/`SHEET_TRANSITIONS` and the
two new sheet procedures (`markPrinting`/`markPrinted`) that move sheets through it — specifically
whether a vendor-path sheet can be forced into (or past) this new state. Full command evidence
(tsc/lint/test/build, scan-test-weakening, the DB-copy pass) is in `T-6-2-reviewer-r1.md`; not
re-run here to avoid duplicating it. This file adds one targeted check that file's finding is
built on.

## 1. The state machine as specced vs. as built
`wave.md`'s stub and this card's contract commit (`b8f6eb5`) agree exactly:
```
ready: ["sent", "printing", "building", "cancelled"],
printing: ["printed", "cancelled"],
```
That part is correct and additive — `SHEET_TRANSITIONS["ready"]` gaining `"printing"` doesn't
change what a vendor-path sheet can reach from `ready` (`sent` is still there), and nothing about
`sent`/`acknowledged`/`printed`/`shipped`/`received` changed at all. Taken purely as a transition
table, vendor-path sheets genuinely cannot enter `printing`.

## 2. Where the safety actually breaks
The transition table isn't the only gate — the two new *procedures* are. `markSheetPrinting`
(`invai-backend/src/modules/production/sheets.ts:1089`) correctly re-checks
`company.settings.printsInHouse` before calling `transitionSheet(..., "printing")`, on top of
`transitionSheet`'s own table check. `markSheetPrinted` (same file, line 1109) calls
`transitionSheet(..., "printed")` with **no equivalent guard** — not a `printsInHouse` check, not
even a check that the sheet's current state is `printing`. Because `printed` is already a valid
`SHEET_TRANSITIONS` target from `sent` and `acknowledged` (that's how the *vendor* path always
reached `printed`, via `invai-web`/vendor-webhook code calling `transitionSheet` directly — never
through a user-facing procedure before this card), the new `production.sheets.markPrinted`
endpoint is reachable from those vendor states too, and the transition-table check alone lets it
through.

I confirmed this live (DB copy `invai_t62r_copy`, API on :3193): sheet `#25` (vendor "Sun City
DTF", status `sent`, company `printsInHouse: false`) accepted a direct
`POST /production/sheets/{id}/mark-printed` and moved to `printed` with a stamped `printedAt` —
no vendor confirmation, no `printing` state, no error of any kind. The UI's own gating (the "Mark
printed" button only renders when `sheet.status === "printing"`,
`invai-web/src/routes/_app/production/sheets.$sheetId.tsx`) is real but client-side only; nothing
stops a direct API call, and `production.build` is a normal office/owner permission, not
vendor-only.

## 3. Why this matters for the invariant being protected
The card's own framing — "the vendor path is unchanged" — is the invariant this state machine
exists to protect: a shop that hasn't opted into in-house printing should have no way to short-
circuit its vendor's confirmation. This gap doesn't let a sheet *enter* `printing` improperly (the
transition table genuinely blocks that), but it lets a vendor sheet reach the *end state* the
`printing` path was built to reach, by a different route, with none of that path's checks. The
practical effect is identical to the one the wave was trying to prevent: a sheet gets marked
`printed` — and its transfers subsequently receivable via the ordinary `printed → received` flow —
without ever actually being printed by anyone.

## Recommendation (not a fix I'm applying — owner's to make)
`markSheetPrinted` should refuse unless `sheet.status === "printing"` (a plain `INVALID_TRANSITION`
would do, since `transitionSheet` already throws that shape for other invalid states — it just
isn't given the chance to here because `printed` is reachable from more than one state). That one
extra check closes the gap without touching the transition table or the vendor's own webhook path.

## Checks
- [x] `SHEET_STATES`/`SHEET_TRANSITIONS` shape matches `wave.md` verbatim (checked against
  `invai-contracts` `b8f6eb5`'s diff to `states.ts`).
- [x] `ready → printing` is correctly gated by `printsInHouse` (`markSheetPrinting`); confirmed
  `FORBIDDEN` live when the setting is false.
- [ ] `printing → printed` (and, transitively, any state `→ printed`) is *not* correctly gated —
  see above. This is the box that fails.
- [x] Vendor's own `sent/acknowledged/printed/shipped` transitions (`invai-backend/src/modules/vendors/service.ts`)
  are untouched by this card's diff.

## Blocking findings
1. Same as `T-6-2-reviewer-r1.md`'s finding 1: `invai-backend/src/modules/production/sheets.ts:1109`
   (`markSheetPrinted`) needs a guard — either `printsInHouse` or `sheet.status === "printing"` —
   before this card can land. See that file for the exact repro.

## Optional notes (not blocking)
- Once fixed, worth a backend test that specifically calls `markSheetPrinted` from `sent` and from
  `acknowledged` on a non-in-house company and asserts it's refused — the existing
  `print-bins.test.ts` only tests the happy path (`ready → printing → printed`) and a non-`ready`
  refusal on `markSheetPrinting`, not `markSheetPrinted`'s own guard. That gap in coverage is what
  let this through.
