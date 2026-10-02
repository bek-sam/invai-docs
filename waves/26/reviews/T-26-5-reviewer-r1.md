# Review of T-26-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web: pnpm typecheck && pnpm lint && pnpm vitest run --reporter=dot` | exit 0; 24 files, 163 tests passed (lint shows only a pre-existing info hint) |
| i18n diff 66ab0cb~1 → 66ab0cb (node: flatten en/es/i18n-es.json) | keys 2273→2353 in all three; 0 missing; es==en count 40→40 (unchanged); json==es |
| 109 `t("…")` keys used by the new files vs en.ts | all present except `common.error` (pre-existing gap, also in states.tsx) |
| `scan-test-weakening.sh invai-web 66ab0cb~1` | only hit is QA's 760d6f4 e2e (loose regex → exact "No access"; stronger). This commit touches no e2e/tests |
| backend `photos/service.ts:279-283,846-865`, imaging `app/photos.py:54-62`, `contracts/roles.ts` | read: analysis/zip/presign semantics, preset mirror (matches), photos.read ⇒ manage for every shop role, none for floor roles |
| Screenshots `/tmp/t265/shot1`, `shot6` | read: see findings 3–4 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | nav.ts entry `photos.read` (floor roles lack it); route shows FORBIDDEN via listSets ErrorState; design detail button with `designId` |
| 2 | yes | PickDesign search + thumbnails (but see finding 3) |
| 3 | partly | pending poll + sample badge + swatches + warnings shown (shot1); failure path unreachable and loops (finding 1); warnings name no fix ("Try Black or Navy") |
| 4 | partly | estimate live (shot1); short-credit reason only in a `title` tooltip on a disabled button (:532), invisible on touch/keyboard |
| 5 | yes | grouped grid, check messages, 2.5 s poll + realtime |
| 6 | partly | approve/reject/attach OK; zip can be stale or spin forever (finding 2) |
| 7 | yes | `creditKind.photo_image/photo_scene` in en, es, json |
| 8 | no | finding 4 |
| 9 | no | shot6: "tee · White" untranslated, grid 2 columns at 390 px, Attach button overflows the card (finding 4) |

## Blocking findings
1. `listing-photos.tsx:221-226` — `analyzeDesign` (a credit-checking POST) is polled every 2 s while `pending`. Backend (`service.ts:279-283`) answers a `failed` row with a NEW enqueue + `pending`, so `status: "failed"` never reaches the UI (the :258 branch is dead). Scenario: imaging returns a permanent 4xx or the AI spend cap is hit → job fails → next poll re-enqueues → imaging + AI route rerun every ~2 s for as long as the tab is open, with a spinner forever. Stop polling when `jobId` changes (previous job failed) and show a retry state; raise the backend semantics with the tech lead (T-26-4 owner).
2. `listing-photos.tsx:591-601,644-652` — zip re-export is keyed on the approved COUNT, not the approved id set, and has no failed state. Scenarios: (a) while the zip builds, approve C then reject A → count unchanged → the ready zip still holds rejected A and "Download zip" serves it (AC6). (b) `exportZip` errors or `zip.status === "failed"` → no retry, "Building zip…" spinner forever, `zip.error` never shown. Key on sorted approved ids; render failed with retry.
3. `listing-photos.tsx:160-167,715` — signed-URL storms (lesson 2026-10-01 P1 / B-209). (a) PickDesign mounts `SignedImage` for all 30 cards at once; `designs.index.tsx:58-90` already fixed this with `useInView`. (b) `getSet` re-presigns every URL on each 2.5 s poll and each realtime invalidation (`presignGet` has a new X-Amz-Date), so every rendered 1600–2700 px photo's `src` changes and re-downloads every poll while a set renders or zips. Reuse the lazy pattern; keep a URL per image id until it nears expiry.
4. AC8/AC9 raw English and layout: `labels.ts:176` falls back to the server text for NOT_FOUND ("photo set <uuid> not found" when `?setId=` is stale) and for BAD_REQUEST without `data.reason` (plain input validation); `:736` shows `image.error` (e.g. "The image service is not responding…") and `:262` `analysis.data.error` verbatim in the es UI; `:727` prints the raw enum `tee`/`hoodie` (use `garmentLabel`); `:160,674` `grid-cols-2` at 390 px where AC9 asks one column, and shot6 shows the Attach button running past the card edge. Map these to translated generic messages.

## Checks
- [x] Only owned paths changed (9 files under src/, scripts/i18n-es.json; no e2e)
- [x] Nothing outside scope (no scenes, no Shopify push)
- [x] Tests exercise the behavior, and none were weakened (no unit tests added for `labels.ts`; non-blocking)
- [x] Tenancy n/a (web only); createSet idempotency key stable per spec; en/es complete; no toLocale*/Intl in new code
- [x] Decisions: preset mirror documented in code; matches imaging today

## Optional notes (not blocking)
- Preset mirror (`labels.ts:63-71`): numbers match `app/photos.py` today; ask backend to fill `PhotoCheckFailure.detail` so the mirror can go.
- Plurals: "1 photos, 1 credits", "{{count}} photo still needs approval" need `_one/_other` keys.
- Realtime `photo_set.updated` → `orpc.photos.key()` also refetches the analyzeDesign POST; narrow to `getSet`/`listSets`.
- `common.error` is missing from en/es (pre-existing); the :736 fallback shows the raw key.
