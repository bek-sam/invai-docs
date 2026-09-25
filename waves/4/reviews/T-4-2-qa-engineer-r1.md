# Review of T-4-2 (round 1)

- Reviewer: qa-engineer on Fable
- Author: floor-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
Same setup as the primary reviewer (shared to avoid re-cloning the DB twice): worktrees `invai-floor-t42-r1` @ `aba5ccf`, `invai-backend-t42-r1` @ `bdffe6f` (HEAD), `node_modules` symlinked. DB copy `invai_r42_copy` (`docker exec local-postgres-1 createdb -U invai -T invai invai_r42_copy`, migrated). API :3193, `REDIS_URL=redis://localhost:6379/11`, floor :5193.

| Command | Result |
|---|---|
| `invai-floor-t42-r1$ ./node_modules/.bin/vitest run --passWithNoTests` | 6 files, 71 passed |
| `invai-floor-t42-r1$ ./node_modules/.bin/vite build` | built, 265.43 KB gzip main chunk |
| `E2E_FLOOR_URL=http://localhost:5193 E2E_API_URL=http://localhost:3193 ./node_modules/.bin/playwright test e2e/offline.spec.ts e2e/press.spec.ts` | 2 passed (7.4s) — `offline.spec.ts` alone 4.1s |
| Read `e2e/offline.spec.ts` step by step against the card's step 7 ("offline → scan 3 units → one server-rejected entry → reconnect → 2 sync, 1 parked, the alert shows, and nothing jams") | matches exactly: parks the on-hold unit, alerts it, syncs the other two, and a 4th live scan after reconnect gets a normal PRESS |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor-t42-r1 04b34d9` | 5 removed assertions, all superseded by stronger tests after a documented, intentional behavior change (auth-failure handling moved from "stop the whole flush" to "park just that entry") |
| Ad hoc scratch test (written, run, deleted, never committed): `engine.submit()` under a permanent 500, flushed 5x | `useSyncStore.getState().alerts` contains the `gave_up` entry — proves Blocking finding 1 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Parking | yes | Unit tests cover 5xx backoff-then-park, 408/429 treated the same, timeout counts as an attempt but offline doesn't, any other 4xx parks at once (incl. 403/404) |
| 2 Problems sheet | yes | Unit tests for retry/discard/lead-gating/pruning; screenshots show what/when/who/why in both languages |
| 3 Rejected replays | **partially** | The E2E's one tested case (order-hold BLOCKED) is correct and clearly worded. But the alert also fires for outage give-ups that were never rejected — see Blocking finding 1, and my ruling on the card's outage question below |
| 4 Attribution | yes | Unit tests for never-resend-as-current-user, same-person-same-station resume, lead-explicit send-as-me |
| 5 Forgetting the station | yes | Unit test + screenshots; the E2E doesn't cover this path directly but the report's real-stack run does (`E:parked:station_forgotten`, never replayed) |
| 6 `storage.persist()` | yes | requested at pairing; grant outcome is device-dependent, correctly caveated, not testable headless |
| 7 E2E `offline.spec.ts` | yes | Re-ran myself, passed, `press.spec.ts` unaffected |

## Blocking findings
1. `src/outbox/sync.ts:177` — the `rejected` filter that feeds the full-screen `ReplayAlert` (`SyncStatus.tsx:394-410`, copy at `en.ts:97-103`/`es.ts:100-106`) includes `parkReason === "gave_up"`, not just `"rejected"`/`"blocked"`. A `gave_up` entry never received a server verdict — it's exactly the "overload" case floor-engineer.md rule 6 says must not read as an error. I proved this with a throwaway test: `engine.submit()` under a permanent 500 error, flushed 5 times, lands the `gave_up` entry in `useSyncStore().alerts`, which drives "1 offline scan was rejected — find this unit and set it aside" with the error sound. **Concrete failure scenario:** the API restarts for 90 seconds mid-shift. A press scan that was almost certainly correct gives up after 5 attempts (no verdict either way) and the tablet tells the presser, in red, with a sound, to pull the shirt and set it aside — a false and disruptive instruction caused purely by a brief outage, not by anything wrong with the unit. See my ruling on decision 3 below for the required fix and what I am *not* asking to change.

## Checks
- [x] Only owned paths changed: `e2e/offline.spec.ts` (qa-engineer co-owns this file; I reviewed it as both author-adjacent and reviewer), `src/app/actions.ts`, `src/components/SyncStatus.tsx`, `src/i18n/{en,es}.ts` (own hunks), `src/outbox/**`, `src/screens/LoginScreen.tsx`
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened: the scan script's hits are all accounted for by a documented, intentional behavior change with equal-or-stronger replacement coverage (see the reviewer file for the full breakdown; I independently reached the same conclusion). Deterministic: unique `clientScanId`s, `expect.poll`/`waitFor` used in the E2E rather than sleeps, `sortBy("seq")` keeps ordering explicit in every test
- [x] The E2E is a real acceptance test of card step 7, not just a smoke test: it asserts server-side state (`state(a.orderItemId)` etc.), not just UI text
- [x] `press.spec.ts` still green after T-4-2's changes — no regression to the existing golden scan-flow path
- [x] Decisions recorded where needed

## My ruling on decision 3 (outages)
The card's AC1 explicitly specifies "up to 5 attempts, then parked" for a 5xx/408/429, and the resulting ~90s-per-entry-before-parking is a defensible trade-off: an ordinary blip self-heals well inside 90 seconds without ever parking, and once parked, "Try all again" recovers everything in one tap — nothing is lost, contrary to what an unlimited-backoff-forever design would risk (a truly dead server would leave scans silently "retrying" forever with no visible signal a lead needs to look). **I do not require replacing parking with unlimited capped backoff.** What I do require, as the blocking finding above, is that a `gave_up` park (no server verdict) stop being presented to the presser as if the server had rejected the unit — that conflation is the actual rule-6 violation, not the parking policy itself. Concrete rule: **only `parkReason` values `"rejected"` and `"blocked"` (an actual server verdict on the unit) may populate `alerts`/trigger `ReplayAlert`; `"gave_up"` and `"station_forgotten"` must never raise that dialog or use "was rejected" language.**

## Optional notes (not blocking)
- Consider a small "server outage" case in `offline.spec.ts` (or a lower-level `sync.ts`/`outbox.ts` test, already partly covered by unit tests) that specifically exercises `gave_up` end to end through the UI, once finding 1 is fixed, so this class of bug doesn't recur.
- The straddling-upgrade edge case noted in the primary reviewer's file (a pre-migration `pending` row that later hits a 401 has no `stationId`, so it can only be discarded, not resent) is real but narrow; I'd file it as a follow-up rather than block on it.
