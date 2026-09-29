# Review of T-22-1 (round 1)

- Reviewer: web-engineer on Sonnet 5
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts log --oneline -8 origin/main` | HEAD `78d2469` (revert of gated fee commit), `184149c` (revert of gated reasons commit) atop `f519085`; working state = 0.8.0 minus the two gated commits, as the card states |
| `node -p "require('./package.json').version"` (contracts) | `0.8.0` |
| `invai-web` links `@invai/contracts` → `../../../invai-contracts` (real dir, not stale symlink) | confirmed, matches origin/main; no unmerged cherry-picks present |
| `cd invai-web && pnpm typecheck` | `tsc --noEmit` clean |
| `cd invai-web && pnpm lint` | `Checked 176 files. No fixes applied. Found 1 warning.` (pre-existing test-file style nit, unrelated to this card) |
| `cd invai-web && pnpm test` | `Test Files 19 passed (19) / Tests 117 passed (117)` |
| `cd invai-web && pnpm build` | fails: `VITE_API_URL must be set...` — from unpushed wave-24 commit `c1d53a8` (CSP), out of scope per my instructions |
| `cd invai-web && VITE_API_URL=https://api.example.com pnpm build` | succeeds, `✓ built in 1.91s` |

## Acceptance criteria (web-consumer angle only; others already approved)
| # | Met? | Evidence |
|---|---|---|
| 7 (web typecheck against 0.8.0) | yes | `tsc --noEmit` clean, `pnpm build` clean once the unrelated CSP env var is supplied |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (read-only review; nothing edited outside `invai-docs/waves/22/reviews/`)
- [x] Nothing outside scope
- [x] N/A — no tests to weaken; this review re-runs existing suites
- [x] Additive shapes only: `Rate.expiresAt?`, `Org.shipsSaturday?/transferAgeWarnDays?`, `QueueItem.blank.shelf?/binCode?`, `ScanResult` fields all optional; `ListingContent.attributes` unchanged (`Record<string,string>`, ADR 0017) — no breaking change for web
- [x] `MISMATCH_REASONS` gained `station_maintenance` at the tail (additive enum); web's mismatch/reason lookups are `t()` keyed with fallback, so no typecheck break, only an untranslated string until wave 23 adds keys
- [x] Decisions recorded: ADR 0017 (listing attributes) is present and consumed correctly

## Optional notes (not blocking)
- Confirmed `src/lib/realtime.ts` `keysForEvent()` has no case for `station.maintenance_changed` yet (event exists in `src/events.ts`/`src/realtime.ts`). This is already wave 23 T-23-1 AC3 ("`keysForEvent` case for `station.maintenance_changed`"), not a new gap.
- `production.maintenance`, `shipping.scanForms`, `shipping.verifyAddress`, `vendors.sheets.resendEmail` are all usable procedure shapes for wave 23 screens (routes, permissions, error contracts, idempotent-by-result-shape maintenance, present and typed).
- The `pnpm build` failure on plain invocation is the unpushed wave-24 CSP commit's new `VITE_API_URL` requirement, unrelated to this card; noted only so the next reader isn't confused by it.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
