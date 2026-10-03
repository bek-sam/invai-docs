# Review of T-27-3 (round 1)

- Reviewer: reviewer on fable
- Author: backend-engineer (photos) on opus
- Verdict: approve
- Commits: invai-backend 2e14396, ef2a6c5, 228ffa4, 257db89 (`git diff --stat 2e14396~1 257db89`: 14 files, all in `src/modules/photos/**`, `src/db/schema/photos.ts`, `drizzle/0041*` + meta, `src/integrations/imaging/client.ts` additive `photoSceneBase`/`photoSceneComposite` only).

## Evidence I re-ran (keys blanked: `OPENAI_API_KEY= ANTHROPIC_API_KEY=`)
| Command | Result |
|---|---|
| `pnpm typecheck` | exit 0 |
| `pnpm lint` | 500 files, no fixes, exit 0 |
| `pnpm vitest run --reporter=dot src/modules/photos src/db` | 110 passed, exit 0 (rls-coverage included) |
| `pnpm vitest run --reporter=dot src/api/authz.test.ts` | 7 passed |
| `scan-test-weakening.sh invai-backend 2e14396~1` | 0 removed assertions, +117; mocks are on deps only (`getImageProvider`, S3, imaging spies, attach); `if (!env.isTest)` scheduler guard is the house pattern (privacy, today, digest, shipping jobs) |
| psql dev DB (author's set a0de3606) | 2 `ai_scene` comps: attempt 1, scene stored, charged once (10 each), `contains_person` t/f by kind; 4 AI images approved, lock 0.986–0.987; `photo_pushes`: failed (http blocker), pushed 3/0, pushed 0/3 skipped; 3 `photos.pushed_to_shopify` audit rows; 2 `image_scene` ai_jobs |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `service.ts` createSet: `assertImageGenAllowed(scenes + open.scenesPending, heldCredits incl. template credits)` before any insert/emit; test "refuses before anything is written" (cap, then credits) |
| 2 | yes | `scenes.ts`: row `sceneKey` then S3 `headObject` before any provider call; `recordImageGen` on success and on throw; drift at attempt 1 → `sceneAttempt=2, sceneKey=null` → one regenerate; attempt 2 drift → all outcomes failed → `recordRenders` charges only when some image is DONE, under charge lock + set/comp `FOR UPDATE`, `chargedAt IS NULL`, kind `photo_scene`, ref `{photo_scene, id}`; XMP subject from `containsPerson` (kind at createSet, provider result after). Tests: drift once/twice, retry after lost composite (provider called once), dev rows above |
| 3 | yes | `attachToDraft` passes `aiGenerated`/`syntheticPerformer`; `zip-readme.ts` README.txt per channel, en + es, lists AI and synthetic-person files; tests "attach sends…", "zip gets a README", "entries append as valid stored entries" |
| 4 | yes | `push.ts`: listing under RLS (foreign → NOT_FOUND), same `connectionId` + channel shopify + numeric id → `gid://shopify/Product/<id>`; approved + `<imageId>.jpg` only; `(company_id, idempotency_key)` unique + request hash → CONFLICT; audit row; job `pushing`/FINAL status guard, presign 6 h (`PUSH_URL_TTL_S`), adapter dedupes by filename → `already_pushed`; `getSet().pushes`. Test "pushes once; retry pushes nothing twice", "presser FORBIDDEN; another company NOT_FOUND"; dev rows above |
| 5 | yes, with known gap | Dev DB rows above; `IMAGE_GEN_MOCK_DRIFT=1` test uses the real mock. Mock Shopify rejects http presigned URLs (channels follow-up, not this card) |
| 6 | yes | `attachToDraft` CONFLICT on `draft.designId !== s.designId`; test |
| 7 | yes | `estimate` subtracts `openCommitments` (now scene-aware `openWork`); test |
| 8 | yes | claim step (`renderScene` step 1 and attempt-2 path) takes `lockCompanyCharges` then `sceneRefusal` → `assertImageGenAllowed` before the provider; tests "claim step … never calls the provider", "daily cap refuses a claim" |
| 9 | yes | `analyzeDesign`: `row.status === "failed"` returned inside `if (row && !input.refresh)`; test |
| 10 | yes | 14 lifestyle tests + retention run-twice; `purge.ts` reads ids with `withSystem` (reason comment), deletes only `isCompanyKey` keys, writes under `withTenant` |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (step 8 base-tree run skipped: the module and every export are new, so the tests fail trivially on base; the drift/idempotency assertions are on provider call counts)
- [x] Tenancy (`withTenant` on both routes; `photo_pushes` has company_id, RLS policy, composite set FK, company-first indexes), idempotency (push key + hash, scene row/S3 guard, charge under lock), money in credits/cents, en/es README
- [x] Decisions recorded where needed (ADR 0023 §9 retention; no new decision needed)

## Optional notes (not blocking)
1. `scenes.ts:344,357` — `recordImageGen` is not given `sizePx` (wave log 2026-10-03: "must pass the real sizePx"). Harmless today because `SCENE_SIZE_PX` = 1024 = the default used by `failedCallCents`; one-line fix so a future size change can't under-count failed-call spend.
2. `scenes.ts:320` — a scene adopted from S3 after a crash keeps `sceneModel` "unknown" and has no `ai_jobs` row (report gap 3); the person flag is safe (kind-based at createSet).
3. `push.ts:374` — the adapter key is per (set, listing, image-set) with per-image filename dedupe, since `pushProductImages` takes one key per call (wave.md interface). Fine as a reading of AC4.
4. `purge.ts:99` — purging a composition that still has open images (job stuck > 7 d) nulls `sceneKey`, so a later retry would call the provider again (re-checked under the lock, so bounded).
