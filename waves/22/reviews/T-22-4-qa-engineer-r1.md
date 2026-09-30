# Review of T-22-4 (round 1) — floor co-review

- Reviewer: qa-engineer on Opus 5.5 · Author: backend-engineer on claude-opus-5-5
- Verdict: **approve**
- Scope: floor golden path against this card's API, plus independent proof of AC3 (maintenance block
  and offline-replay parking) on a fresh seed. `reviewer` (r1 changes-required, r2 approve) and
  `backend-foundation` (r1 approve, migration) already covered code-level correctness and the migration;
  this review adds the gate's fresh-seed floor suite and my own curl reproduction of the round-2 fix.

## Evidence I re-ran
| Command | Result |
|---|---|
| Fresh reset/migrate/seed (`invai-backend`, imaging running) then `cd invai-infra && pnpm dev:all` | seed done: orders 360, items 694, transitions 3935; personalized artwork 59/59 rendered; sheet files composed 4/4 (25 sheets, 597 transfers); health `db/redis/imaging/s3: true` |
| `cd invai-floor && pnpm e2e` | 3 passed (10.6s): `floor.spec.ts` (pack blocks on a missing unit), `offline.spec.ts` (offline scans replay in order, a server-rejected one is parked and alerted), `press.spec.ts` (station setup, PIN login, press scan check, QC pass, pack) |
| `cd invai-web && E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` | 13/13 (16.0s), incl. step 8 floor PIN/wrong-size-BLOCKED/press/QC/pack |
| curl: office@ starts maintenance on Press 1, presser@ (floor session) scans a correct blank at Press 1 | `ok:false, mismatch:"station_maintenance", itemState:"transfer_in", nextAction:"press"`, plain-language message "This station is under maintenance. Use another station." |
| curl: office@ ends maintenance (real time), then a *new* scan with `scannedAt` set inside the now-past window (simulating an offline scan synced late) | `ok:false, mismatch:"station_maintenance"` — the item stays `transfer_in`, not pressed. This is the exact AC3 offline-replay scenario reviewer r1 found broken and r2 fixed (`03d780e`) |
| curl: same presser, same station, a scan with `scannedAt` after the window | `ok:true, itemState:"pressed", nextAction:"qc"` — normal operation resumes once the window and the scan's own time are both clear |
| curl: pick queue (`production.queue` station=pick) | `transferAgeDays`/`transferAgeWarning` present on every line (AC2); `binCode` present and `null` where the seed sets no bin (AC4 field wiring correct; no populated example in seed data, matches the author's reported gap) |
| psql as `invai_app`, `app.company_id` = Sun City DTF, insert `station_maintenance_events` referencing Desert Bloom's Press 1 station id | `ERROR: insert or update on table "station_maintenance_events" violates foreign key constraint "station_maintenance_events_station_id_fk"` — cross-tenant composite FK correctly refused |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | already proven (reviewer r1/r2, backend-foundation) | not re-run here; QA scope is floor/AC3 |
| 2 | yes (spot-checked) | pick queue lines carry `transferAgeDays: 0`, `transferAgeWarning: false` on fresh (same-day-printed) transfers |
| 3 | **yes** | live-window block reproduced; offline-replay-after-window-ended block reproduced (the r1 finding, now fixed); post-window scan proceeds normally; floor's own offline outbox (`offline.spec.ts`) still parks a server-rejected scan and alerts, unaffected by this card |
| 4 | field wiring yes; no populated example available | `binCode` returned (null) on pick lines; a live curl with a non-null bin was not attempted — the sandbox correctly blocks ad-hoc writes to the shared dev DB, and the author's own report + reviewer r1's evidence table already show a populated `B-03-3 / TOTE-B12` case, which I did not need to duplicate |
| 5 | yes | floor golden path 13/13 and the 3 floor E2E specs all pass against this card's API on a fresh seed; no tenant leakage observed in any call above |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (already confirmed by `reviewer` r1/r2 and `backend-foundation` r1; not re-diffed here)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; floor's offline/press/pack suites are unmodified and green against this card
- [x] Tenancy: cross-tenant composite FK insert refused as `invai_app`; maintenance/scan procedures scoped by `company_id`
- [x] Decisions recorded where needed (none new from this review)

## Optional notes (not blocking)
- The pick-queue `binCode` acceptance case has no live example in the current seed (author's own "Known gaps": no contract procedure sets bins, only seed/service code). Not a T-22-4 defect; a seed/inventory-screen follow-up already noted in the author's report.
- Digest-dates browser tests (`e2e/digest-dates.spec.ts`, T-20-2, unrelated to this card) failed on this same fresh seed: `/digests` has no row yet. This looks like the known digest-sweep timing dependency already noted in the wave 20 gate (`qa-report.md` §9), not something T-22-4 touches. Filed to the tech lead in `gate.md`, not blocking this card.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
