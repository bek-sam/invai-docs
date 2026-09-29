# Review of T-22-1 (round 1)

- Reviewer: backend-foundation on Sonnet 5
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-contracts && git log --oneline 83eee25..HEAD` | 5 commits: `f519085` (0.8.0 base), `83013af`/`78d2469` (REPRINT_REASONS add + revert), `81afad4`/`184149c` (TikTok fee add + revert) |
| `cd invai-contracts && git diff --stat 83eee25..HEAD` | net diff at HEAD == `f519085` alone (17 files, 746+/14-); confirms the two gated patches cancel exactly, nothing else leaked in |
| `cd invai-contracts && pnpm typecheck` | clean |
| `cd invai-contracts && pnpm test` | `Test Files 8 passed (8) / Tests 87 passed (87)` |
| `cd invai-backend && pnpm typecheck` | clean (0 errors) |
| `cd invai-web && pnpm typecheck` | clean (0 errors) |
| `cd invai-floor && pnpm typecheck` | clean (0 errors) |
| `cd invai-backend && vitest run src/api/authz.test.ts src/api/orpc.test.ts` | `Test Files 2 passed (2) / Tests 8 passed (8)` — authz walks every procedure incl. the new `production.maintenance` permission and the four stub procedures |
| `cd invai-backend && git show 2cda6e2` (full diff) | matches its stated grant exactly: `production/router.ts`, `shipping/router.ts`, `vendors/router.ts`, stub lines only, using the existing `stubRouter()` helper in the documented pattern |
| Applied and reverted `83013af`/`81afad4` by inspection (`git show`) | each revert is the exact inverse diff of its patch; re-applying either via the report's named cherry-picks is mechanical |
| `grep -n "REPRINT_REASONS" invai-backend/src/db/schema/production.ts` | still the 12 old values, no `under_cure`/`cracking` — confirms the gate is real (main's backend mirror hasn't moved) |
| `sed -n '85,95p' invai-backend/src/modules/finance/fees.test.ts` | still asserts `toBe(8)` — confirms the fee gate is real |
| `grep -n station_maintenance_events invai-backend/src` | no hits — table correctly left for T-22-4, contract doesn't presuppose it |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 shipping (scanForms, verifyAddress, Rate.expiresAt) | yes | `contract/shipping.ts`/`schemas/shipping.ts` diff: 3 procedures + `AddressVerification`, `Rate.expiresAt?` optional (server judges on buy, backend without it still typechecks) |
| 2 production (qc reuse, maintenance, station_maintenance mismatch) | yes | `production.qc`/`reprintReason` untouched (no new `qcFail`, matches architect's plan-review resolution item 2); `production.maintenance.start/end/list` on a new `StationMaintenance` schema, doc comment explicit that it's backed by `station_maintenance_events`, production-owned (A3); `MISMATCH_REASONS` gets `station_maintenance` appended, `ScanResult`/`QueueItem` only gain optional fields — a scan never throws for this (A4 satisfied; card text and implementation both say `station_maintenance`, not the plan-review draft's `station_blocked_maintenance` — the card is authoritative and matches) |
| 3 inventory (pick line binCode/shelf) | yes | `QueueItem.blank.shelf?/binCode?` and `ScanResult.expected.shelf?/binCode?`, nested under `blank` specifically to avoid colliding with the existing top-level `QueueItem.binCode` (the pack tote) — correct, would have been a real bug otherwise |
| 4 vendors resendEmail | yes | `vendors.sheets.resendEmail`, `vendors.manage`, `SHEET_NOT_SENT`/`VENDOR_USES_PORTAL`/`RESEND_TOO_SOON` errors |
| 5 OrgSettings shipsSaturday/printsInHouse | yes | diff confirms `printsInHouse` was already settable (untouched by this diff); `shipsSaturday?` and `transferAgeWarnDays?` newly added to `me.updateOrg` input and `Org` output |
| 6 TikTok 6%, ListingContent.attributes | yes (fee gated, correctly) | `81afad4` diff shows source URL + date in both the constant's comment and `schemas.test.ts`; ADR 0017 (`invai-docs/decisions/0017-listing-attributes-shape.md`, accepted, indexed) settles `attributes` as a map with the model's list folded once in `toContent` — no breaking change, `schemas/ai.ts` diff is a doc-comment only |
| 7 checks green everywhere | yes | see Evidence table |

## Backend/web/floor consumer check
- **Backend stubs (T-22-3/4/5's contract to implement):** `2cda6e2` follows the established `stubRouter()` pattern byte-for-byte against its own doc-comment example in `src/api/orpc.ts`. Nothing leaks through `NOT_IMPLEMENTED`: `stubRouter` recurses the contract tree and calls `.handler(() => { throw notImplemented(name) })` on every leaf procedure, so `scanForms.create/list/get`, `verifyAddress`, `maintenance.start/end/list` and `sheets.resendEmail` all throw a typed `NOT_IMPLEMENTED` today, and `authz.test.ts` (which walks every procedure) is green, proving the permission guard runs *before* the stub body — a caller without `production.maintenance`/`shipping.manage`/`vendors.manage` gets `FORBIDDEN`, not `NOT_IMPLEMENTED`. No new procedure was left unstubbed: `inventory` and `tenancy` correctly have no stub because neither got a new *procedure* (tenancy's addition is two new fields on an existing input/output, inventory's is two new fields on an existing schema — nothing to stub).
- **Can T-22-3/4/5 build against this without a further contract change?** Yes, on inspection of each new schema and its doc comments: `ScanForm`/`AddressVerification`/`Rate.expiresAt` give T-22-3 everything named in the card (idempotency key, error shapes, PDF key via `files.downloadUrl`); `StationMaintenance`/`MaintenanceStartResult.started`/`MaintenanceEndResult.ended` give T-22-4 an idempotent-by-shape result and an explicit "production-owned table, not `stations`" instruction matching architect plan-review item 3; `QueueItem.blank.shelf/binCode` and `ScanResult.expected.shelf/binCode` are nested correctly to avoid the tote-`binCode` collision; `vendors.sheets.resendEmail`'s `RESEND_TOO_SOON` carries `retryAfterSec`/`lastSentAt` so T-22-5 doesn't need a new error shape for its 10-minute window. The two gated patches (`REPRINT_REASONS` +2, TikTok fee 8→6) are exact, cleanly-reverting diffs with the target file:line already named (`db/schema/production.ts` `REPRINT_REASONS`, `fees.test.ts:90`), so T-22-4/T-22-5 cherry-pick and land without guessing.
- **Web typecheck:** `pnpm typecheck` in `invai-web` is clean. Checked the specific worry by hand: `keysForEvent(name: string)` in `src/lib/realtime.ts` is a `switch` over a plain `string` parameter (not the `RealtimeEventName` union) with a `default: return []`, so the new `station.maintenance_changed` realtime event does not force an exhaustive case and cannot break typecheck — matches the report's claim.
- **Floor typecheck and the new `MISMATCH_REASONS` value:** `pnpm typecheck` in `invai-floor` is clean. Traced the actual mismatch-copy path: `src/scan/result.ts` builds `reasonKey: \`mismatch.${r.mismatch ?? "unknown"}\`` via template-string interpolation (not a switch on the union), and `PressStation.tsx` renders it with `t(view.reasonKey ...)` through `react-i18next`'s `useTranslation()`, which has no module augmentation in this repo restricting `t()` to known keys — so `station_maintenance` is safe to add without an i18n key existing yet; a missing key falls back to i18next's default (the key itself), not a type or runtime error. This confirms the report's claim that floor's `mismatch` catalog is effectively untyped for this purpose; the raw-key fallback is a real (if minor) UX gap until wave 23 adds the translated string, but it is not a typecheck or crash risk, and the card correctly scoped web/floor i18n additions out of T-22-1.
- No `REPRINT_REASONS` exhaustive switch exists in floor or web either (`ProblemDialog` lists every value from the array directly, not a switch), so the gated `under_cure`/`cracking` addition is equally safe for those two repos once it lands — only the backend's own `enumText` mirror is a true exhaustive/type-level consumer, and that's the one correctly gated.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`invai-contracts/src/**`, `package.json` version, `CHANGELOG.md`, `README.md` — confirmed via `git diff --stat`; backend commit touches only the three router files named in its stated grant)
- [x] Nothing outside scope (no backend/web/floor implementation code, no removed or renamed field)
- [x] Tests exercise the behavior, and none were weakened — `p2-sweep.test.ts` is new and additive; `digest.test.ts`'s version assertion was changed from an exact pin to "at least 0.7.0" using the pre-existing `isContractVersionAtLeast` helper, which is the documented convention for letting the newest wave's test own the exact pin (not a weakening — the exact pin still exists, in `p2-sweep.test.ts`)
- [x] Tenancy / idempotency / money / en-es: no tenant tables touched (contracts repo has none); maintenance start/end and scanForms.create/resendEmail are all specified idempotent by result shape or error, matching `idempotent-side-effect` conventions; no money fields added besides the already-cents `Cents`/`Timestamp` reuse; no UI strings in this repo (i18n correctly deferred to wave 23 web/floor cards, verified above that this causes no typecheck break)
- [x] Decisions recorded where needed — ADR 0017 (accepted, indexed) for the `ListingContent.attributes` question; the `production.maintenance` permission and `station_maintenance` naming choices are recorded in `roles.ts`/schema doc comments and the CHANGELOG

## Optional notes (not blocking)
- `transferAgeWarnDays` on `me.updateOrg`/`Org` is a small, reported widening of AC5 beyond its literal two names (`shipsSaturday`, `printsInHouse`). It's additive and well-motivated (T-22-4 needs a home for the warning threshold), and the report explicitly flags it as strikeable if the tech lead disagrees — no action needed from me, just noting I saw and agree it's harmless.
- Two grants sit outside any wave-22 card's ownership and are correctly called out rather than silently done: the `me.updateOrg` service-layer hunks for `shipsSaturday`/`transferAgeWarnDays` (tenancy, mine) and nothing else. I'll pick this up separately since B-162's web card depends on it; not a blocker for this contract card.
- Backlog candidate (already noted in the report): `invai-backend/src/db/schema/production.ts`'s `REPRINT_REASONS` should eventually import the contract's array as its one source of truth instead of being hand-mirrored — reasonable, not urgent.
