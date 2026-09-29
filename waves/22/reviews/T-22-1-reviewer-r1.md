# Review of T-22-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-contracts && git log --oneline -1 83eee25` / `HEAD` | base `83eee25`; HEAD `78d2469` "Revert ... under_cure and cracking" |
| `cd invai-contracts && git log --stat 83eee25..HEAD` | 5 commits: `f519085` (0.8.0, on main), `83013af` (REPRINT_REASONS add) reverted by `78d2469`, `81afad4` (TikTok fee add) reverted by `184149c`; the two revert diffs are the exact inverse of their adds (same files, same line counts) |
| `cd invai-contracts && git diff 83eee25 HEAD -- src` | full read: additive only — new procedures (`shipping.scanForms.*`, `shipping.verifyAddress`, `production.maintenance.*`, `vendors.sheets.resendEmail`), new optional fields (`Rate.expiresAt?`, `QueueItem.blank.shelf?/binCode?`, `QueueItem.transferPrintedAt?/transferAgeDays?/transferAgeWarning?`, `ScanResult.expected.shelf?/binCode?`, `ScanResult.transferAgeDays?/transferAgeWarning?`, `Org.shipsSaturday?/transferAgeWarnDays?`), one appended enum value (`MISMATCH_REASONS: station_maintenance`, appended last), a new permission (`production.maintenance`), a new event (`station.maintenance_changed`). Nothing removed, renamed or narrowed. `ListingContent.attributes` diff is doc-comment only (no shape change) |
| `cd invai-backend && git show --stat 2cda6e2` | 3 files, all inside the card's grant: `src/modules/{production,shipping,vendors}/router.ts`, stub lines only via the pre-existing `stubRouter()` helper |
| `cd invai-contracts && pnpm typecheck` | clean |
| `cd invai-contracts && pnpm lint` | `Checked 56 files in 41ms. No fixes applied.` |
| `cd invai-contracts && pnpm test` | `Test Files 8 passed (8) / Tests 87 passed (87)` — matches "main working state = commit 1" (gated commits reverted) |
| `node -p "require('./node_modules/@invai/contracts/package.json').version"` in `invai-backend` | `0.8.0`; `node_modules/@invai/contracts` is a symlink to the live `invai-contracts` tree, so consumer checks below are against the reviewed diff, not a stale publish |
| `cd invai-backend && pnpm typecheck` | clean, 0 errors |
| `cd invai-web && pnpm typecheck` | clean, 0 errors |
| `cd invai-floor && pnpm typecheck` | clean, 0 errors |
| `cd invai-backend && pnpm test src/api/authz.test.ts` | `Test Files 1 passed (1) / Tests 7 passed (7)` — walks every procedure including the 8 new ones and the new `production.maintenance` permission; confirms the permission guard runs before the stub body (a caller without the permission gets `FORBIDDEN`, not `NOT_IMPLEMENTED`) |
| `ls invai-docs/waves/22/patches/` | both patches present: `0001-...under_cure-and-crackin.patch` (matches `83013af`), `0002-...TikTok-Shop-referral-f.patch` (matches `81afad4`); headers and diffs match the commits they claim to preserve |
| `git status --short` in contracts and backend | clean — nothing uncommitted |
| `cd invai-contracts && git diff --stat 83eee25 HEAD` | 17 files, all inside owned paths (`src/**`, `CHANGELOG.md`, `README.md`, `package.json`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 shipping | yes | `contract/shipping.ts`/`schemas/shipping.ts`: `scanForms.create/list/get`, `verifyAddress`, `Rate.expiresAt?` — all read in the diff, all additive |
| 2 production | yes | `production.qc`/`reprintReason` untouched (no new `qcFail` procedure); `QueueItem`/`ScanResult` gain only optional transfer-age fields; `production.maintenance.start/end/list` on `StationMaintenance` (doc comment states it's backed by `station_maintenance_events`, production-owned, per A3); `MISMATCH_REASONS` gets `station_maintenance` appended last; a blocked scan stays a normal `ScanResult` (`ok:false`, existing `nextAction:"press"`), never a thrown error (A4) |
| 3 inventory | yes | `QueueItem.blank.shelf?/binCode?` and `ScanResult.expected.shelf?/binCode?`, nested under `blank` specifically so as not to collide with the existing required top-level `QueueItem.binCode` (the pack tote) — verified the top-level field is untouched in the diff |
| 4 vendors | yes | `vendors.sheets.resendEmail`, `vendors.manage`, `SHEET_NOT_SENT`/`VENDOR_USES_PORTAL`/`RESEND_TOO_SOON` (with `retryAfterSec`/`lastSentAt`) |
| 5 settings | yes | diff confirms `printsInHouse` untouched (already settable, as the report states); `shipsSaturday?` and `transferAgeWarnDays?` newly added to `me.updateOrg` input and `Org` output, both optional |
| 6 fees/attributes | yes (fee gated, correctly) | `81afad4` diff: `transactionPct` 8→6 with source URL + fetch date in both the constant comment and `schemas.test.ts`; `grep REPRINT_REASONS invai-backend/src/db/schema/production.ts` still shows the old 12 values and `sed -n '85,95p' fees.test.ts` still asserts `toBe(8)` — the gate is real, main's backend mirrors haven't moved; ADR 0017 accepted and indexed, settles `attributes` as a map with no breaking change (`schemas/ai.ts` diff is doc-comment only) |
| 7 checks green | yes | see Evidence table: contracts typecheck/lint/test green, backend/web/floor typecheck green against the live symlinked contracts, `authz.test.ts` green |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat 83eee25 HEAD` in contracts: `src/**`, `CHANGELOG.md`, `README.md`, `package.json` only; backend `2cda6e2` touches only the three granted router files)
- [x] Nothing outside scope (no backend/web/floor implementation logic, no field removed or renamed)
- [x] Tests exercise the behavior, and none were weakened — `p2-sweep.test.ts` is new and additive (route/permission/auth table, role-matrix negative/positive checks, schema round-trips, enum-tail checks, event/realtime parse checks, exact version pin); `digest.test.ts`'s version assertion moved from an exact pin to "at least 0.7.0" via the existing `isContractVersionAtLeast` helper, with the exact pin now owned by the newest wave's test (`p2-sweep.test.ts` still asserts `0.8.0` exactly) — this is a relocation of the strict check, not a loosening, and I confirmed the strict assertion still exists and passes
- [x] Tenancy / idempotency / money / en-es: no tenant tables in this repo; `maintenance.start/end` idempotent by result shape (`started`/`ended` booleans, never an error on repeat), `scanForms.create` idempotent on (carrier, date), `vendors.sheets.resendEmail` rate-limited via `RESEND_TOO_SOON` — all specified correctly for their T-22-3/4/5 implementers to follow; no money fields added beyond reused `Cents`; no new UI strings in this repo, and I independently confirmed (matching both co-reviewers) that `station_maintenance` and the gated `REPRINT_REASONS` values don't break web/floor typecheck because neither repo switches exhaustively on those enums
- [x] Decisions recorded where needed — ADR 0017 accepted and indexed for `ListingContent.attributes`; the `production.maintenance` permission choice and `station_maintenance` semantics are documented in `roles.ts`/schema doc comments and the CHANGELOG

## Optional notes (not blocking)
- Agree with backend-foundation's note: `transferAgeWarnDays` widens AC5 by one field beyond the card's two named settings (`shipsSaturday`, `printsInHouse`). It's additive, well-motivated (T-22-4 needs a home for the threshold) and the report flags it as strikeable — no action needed.
- Both co-reviews (`T-22-1-backend-foundation-r1.md`, `T-22-1-floor-engineer-r1.md`) independently re-ran the same core checks (typecheck/lint/test across all four repos, `git log`/diff verification of the gate mechanics) and reached `approve` with no findings that conflict with mine.
