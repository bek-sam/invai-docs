# Review: T-22-1 Contract additions for the P2 sweep — floor-engineer co-review (round 1)
Reviewer: floor-engineer on Sonnet 5 (consumer co-review)
Author: architect on fable

## Scope of this review
Consumer check only: does `invai-floor` build cleanly against contracts 0.8.0, and are the pieces wave 23's
floor card needs (`station_maintenance` mismatch, transfer-age fields, pick-line `binCode`/`shelf`,
`production.maintenance.*`) usable without another contract change. Not a full contract review (that's
`reviewer`/`backend-foundation`).

## Verdict: approve

## Evidence I re-ran
| Repo | Command | Result |
|---|---|---|
| invai-contracts (HEAD = `f519085`, gated commits reverted) | `node_modules/.bin/vitest run` | Test Files 8 passed (8) / Tests 87 passed (87) |
| invai-contracts | `node_modules/.bin/tsc --noEmit` | clean, 0 errors |
| invai-floor | `node_modules/.bin/tsc --noEmit -p .` | clean, 0 errors |
| invai-floor | `node_modules/.bin/vitest run` | Test Files 9 passed (9) / Tests 96 passed (96) |
| invai-web | `node_modules/.bin/tsc --noEmit -p .` | clean, 0 errors |

`invai-floor/node_modules/@invai/contracts` is a symlink to the working `invai-contracts` tree (`link:../invai-contracts`), so this is a real consumer check against the reviewed diff, not a stale published version.

## Findings

**1. `git log` matches the report's account.** `git log --oneline 83eee25..HEAD` shows exactly the four commits the report claims: `f519085` (base, on main), `83013af`/`184149c` reverted by `78d2469`/`184149c`... actually order is `f519085` → `83013af` (reprint reasons) → `81afad4` (TikTok fee) → `184149c` (revert fee) → `78d2469` (revert reprint reasons). `package.json` version is `0.8.0` at HEAD, matching the working state. The two gated changes are correctly absent from HEAD's `src/schemas/production.ts` (`REPRINT_REASONS` has no `under_cure`/`cracking`) and `src/contract/channels.ts` fee stays at the pre-change default per the revert commits — consistent with the report's "why the reverts" explanation (keeping every consumer green at the wave gate).

**2. `station_maintenance` mismatch reason is additive and floor-usable as-is.** `MISMATCH_REASONS` in `schemas/production.ts` appends `"station_maintenance"` last (line ~236), with a doc comment naming `invai-floor/src/i18n/{en,es}.ts floor.mismatch.*` as the consumer. `ScanResult.mismatch` is `z.enum(MISMATCH_REASONS).nullable()` — the floor's existing `ProblemDialog`/result-screen code reads `mismatch` generically (`t(\`floor.mismatch.${value}\`)` with a fallback), so no floor typecheck break and no new branch needed to *receive* this value; wave 23 only needs new i18n keys and a sound/color mapping, both inside floor-engineer's normal `build-floor-flow` work. `nextAction` stays `"press"` (an existing value, no `NEXT_ACTIONS` change), so the floor's next-action switch needs no new case either. This satisfies rule 1 (a mismatch must block) at the contract level — `station_maintenance` behaves like every other blocking `ScanResult`, never a thrown error (per architect A4, confirmed in `contract/production.ts`'s doc comment above the `maintenance` router).

**3. Transfer-age fields are present on both `QueueItem` and `ScanResult`.** `QueueItem.transferPrintedAt?`, `transferAgeDays?`, `transferAgeWarning?` and the matching `ScanResult.transferAgeDays?`/`transferAgeWarning?` are optional additions (`schemas/production.ts` ~171–178, ~291–292). Optional and additive: old floor builds parsing these responses are unaffected: this satisfies decision 0012's "additive changes need no compat window" rule, so `FLOOR_COMPAT_BASELINE` correctly stays at `0.3.0` (confirmed via `grep FLOOR_COMPAT_BASELINE` — every occurrence still asserts `"0.3.0"`, including `p2-sweep.test.ts`).

**4. Pick-line `shelf`/`binCode` land under `QueueItem.blank` and `ScanResult.expected`, not top-level.** Confirmed at `schemas/production.ts` ~155–160 (`blank.shelf`, `blank.binCode`) and ~269–270 (`expected.shelf`, `expected.binCode`), both nullable/optional. The report's stated reason — `QueueItem.binCode` (top-level) is already the pack tote — checks out: line 166 shows the existing top-level `binCode: z.string().nullable()` (no `?`, required) is untouched, so no collision and no breaking change to the pack flow's existing tote field. Good call; a top-level clash would have been a real floor bug (packer scanning the wrong bin code).

**5. `production.maintenance.list` has `auth: "floor"`, matching the card's design for tablets to poll closed stations.** Confirmed in `contract/production.ts`: `list: proc("production.read", { auth: "floor" })...`. `start`/`end` are `auth: "user"` (default, `production.maintenance` permission) — correct, since only a lead ends a maintenance window from the web/office side per the card, and the floor only needs to *read* the list. This matches the report's decisions section and needs no floor-side auth change in wave 23.

**6. Offline replay of a `station_maintenance`-blocked scan needs no new outbox state.** Per decision 0012, only breaking changes to floor-facing shapes open a compat window; this whole card is additive (new enum tail value the floor only *receives*, new optional fields, two new procedures the floor doesn't write to except the idempotent `list` read). A `station_maintenance` result offline is just another `ScanResult` with `ok: false` — the existing "checked on this tablet" / later-BLOCKED-alert path (rule: offline press checks are provisional) already covers it with no reducer change. Confirmed this isn't a gap by reading decision 0012 in full: nothing here is a removed/renamed/narrowed/required-field change, so the "N = 14 days" grace-window machinery doesn't apply and doesn't need to be built for this. Parking this for wave 23 (as the card instructs) is sound.

**7. Scope and ownership.** `git diff --stat origin/main` (not re-run here since this is a read-only co-review of already-committed state, but `git log -p` for the touched paths) shows only `invai-contracts/src/**`, `package.json`, `CHANGELOG.md`, `README.md`, and the two grant-scoped backend router stub files named in the card ("grant" line in the intake note) — inside the card's owned paths. No floor files were touched by this card, correctly (`Out of scope`).

## Optional notes (non-blocking)
- The gated `REPRINT_REASONS` additions (`under_cure`, `cracking`) are not yet on `main`; `invai-floor`'s `ProblemDialog` (which lists every `REPRINT_REASONS` value) will need `floor.reason.under_cure`/`floor.reason.cracking` i18n keys once T-22-4's cherry-pick lands, as the report already flags under "What each consumer must do — Floor (wave 23)". Not a blocker for this card; flagging so it isn't missed when T-22-4 merges.
- `transferAgeWarnDays` on `me.updateOrg`/`Org` (beyond the card's two named settings) is a reasonable small addition given T-22-4 needs a home for the threshold, and it's optional/additive. The report already asks the tech lead whether to keep or strike it — no floor impact either way.

## Checklist
- Ownership/scope: within owned paths — yes.
- Additive-only / floor compat: yes, confirmed against decision 0012.
- Floor consumer typecheck + tests: green (re-run above).
- Web consumer typecheck: green (re-run above).
- Idempotency (`maintenance.start/end` result-shape idempotency, `scanForms.create` idempotent on carrier+date): reviewed by report description; not independently re-tested here since no backend implementation exists yet to exercise (still `NOT_IMPLEMENTED` stubs) — out of scope for this consumer check, in scope for `reviewer`/`backend-foundation`.
- en/es: no floor strings added by this card (contract only); wave 23 owns adding them.

## Blocked by other owners
- none.
