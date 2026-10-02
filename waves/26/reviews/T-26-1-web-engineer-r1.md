# Review of T-26-1 (round 1)

- Reviewer: web-engineer on Sonnet 5
- Author: architect on Fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show --stat 9026680` | 14 files, new `contract/photos.ts` (164 lines) + `schemas/photos.ts` (516 lines) + `photos.test.ts` (435 lines), additive edits to `ai.ts`, `events.ts`, `realtime.ts`, `roles.ts`, `index.ts`, `compat.ts` (0.11.0→0.12.0) |
| `cd invai-contracts && pnpm typecheck` | clean, no errors |
| `cd invai-web && pnpm typecheck` | clean, no errors (consumer repo had no uncommitted edits from the T-26-5 builder yet — `git status --short` empty, so this is a true green, not an artifact of timing) |
| `grep -rn "CHANNELS\|Record<Channel" invai-web/src` | no exhaustive switch or `Record<Channel,…>` map; all usages are `.map()`/`.filter()` over the array, unaffected by `PHOTO_CHANNELS` being a new subset |
| `grep -rln "CREDIT_KINDS\|creditKind\." invai-web/src` | one hit, `billing.tsx:480` — `t(\`creditKind.${kind}\`, kind.replace(/_/g," "))`, a template-key lookup with fallback, not a `Record`; new `photo_image`/`photo_scene` kinds render with the raw-text fallback until T-26-5 adds the i18n keys (expected, named in ADR 0023 "Follow-ups" and T-26-5 AC7) |
| Read `decisions/0023-listing-photos-pipeline.md` | covers design lock, two-check drift, disclosure source-of-truth, approval gate, credits/charge guard, queue pattern, `productRef`, rate buckets, retention — and names the exact web follow-ups (`keysForEvent` case, credit-kind labels) |

## Acceptance criteria (web-consumer view)
| # | Met? | Evidence |
|---|---|---|
| Analysis pending/ready union buildable | yes | `DesignPhotoAnalysisResult` is a `discriminatedUnion("status", …)` with `ready`/`pending`(`jobId`)/`failed`(`error`); `jobId` matches the existing `JobRef` poll pattern already documented in `schemas/common.ts` ("Poll `production.jobs.get`"), so T-26-5 step 2 polling isn't a new pattern to invent |
| Estimate buildable | yes | `PhotoEstimate` carries `compositions`, `images`, `credits`, `creditsRemaining`, `canAfford` (pre-computed bool) and `skipped[]` with a closed `PHOTO_SKIP_REASONS` enum — the "N photos, M credits" line and the disabled-button reason (AC4) need no derived math on the web side |
| Set/image statuses for progress | yes | `PhotoSetStatus`, `PhotoImageStatus` + `PHOTO_IMAGE_TRANSITIONS`, and `PhotoImageCounts` on `PhotoSetSummary`/`PhotoSet` give the web a ready-made progress tally without re-deriving it from the image array |
| Check codes → plain sentences | yes | `PHOTO_CHECK_CODES` is a closed, append-only enum with `severity` (`error`/`warn`) and a `detail` string already formatted by imaging ("fills 78%", "1400 px"); matches the card's example copy almost verbatim |
| Typed error data for translation | yes | `PHOTO_BAD_REQUEST.data = {reason: enum(PHOTO_BAD_REQUEST_REASONS), count}`, `IMAGE_CAP_ERRORS.data = {cap, used, resetAt}`, plus reused `CREDIT_ERRORS`/`SPEND_CAP_ERRORS` (now exported from `contract/ai.ts`) — same shape family the web already maps for AI listings, so no new error-mapping pattern needed; `COMMON_ERRORS` (`CONFLICT`, `NOT_FOUND`, …) apply to every procedure by default, covering the "draft is publishing → CONFLICT" case the `attachToDraft` doc-comment promises even though it isn't in the procedure's own `.errors()` call |
| Signed URLs | yes | `PhotoImage.url`/`PhotoZipState.url` are `nullable`, documented "only from `getSet`"; `PhotoSetSummary.leadImageUrl` gives the list screen one thumbnail without a second request |
| pushTargets / pushToShopify | yes | `pushTargets` returns `PushTarget[]` with `matchesDesign` pre-sorted first; `pushToShopify` takes `productRef: {listingId}` + `idempotencyKey`; a second push's already-pushed images come back in `skipped: [{imageId, reason: "already_pushed"}]` on `PhotoPush`, which directly satisfies T-27-5 AC5 ("a second push shows them as already there") without the web having to infer dedupe from status alone |
| Realtime event | yes | `photo_set.updated` carries `{setId, designId, status, rendered, failed, total}` — enough to drive a progress bar and decide when to refetch `getSet`, and the ADR explicitly calls out the `keysForEvent` case as T-26-5's job |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`invai-contracts/src/**`, no edits outside)
- [x] Nothing outside scope (phase A+B shapes only, as the card asks; no backend/web/imaging code)
- [x] Tests: `photos.test.ts` added (435 lines); not independently re-run line-by-line here (consumer review focus was typecheck + exhaustive-switch scan per task scope), but `pnpm typecheck` across contracts and web is clean
- [x] Enums are additive (`CREDIT_KINDS`, `CHANNELS` untouched, `PHOTO_CHANNELS` is a new `satisfies readonly Channel[]` subset); `ListingDraft.imageDisclosures` is `.optional()`
- [x] Money: none in this contract (credits are integers, colors are `#rrggbb`, sizes untouched) — matches AC3
- [x] Decision recorded: `decisions/0023-listing-photos-pipeline.md` + index row, covers every item the card's AC4 lists

## Optional notes (not blocking)
- `too_many_compositions` is both a `PHOTO_BAD_REQUEST_REASONS` value and enforced by `PhotoSetSpec`'s own Zod `.refine()` (garments × colors × views ≤ 48), so it looks currently unreachable as a server-thrown error for `createSet`/`estimate` inputs that already pass schema validation. Harmless for the web (the reason string still needs a translation either way) — worth a one-line note to backend-engineer (T-26-4) on whether it's reachable through some other combination (e.g. lifestyle + template totals) or just defensive.
- `attachToDraft`'s doc comment promises `CONFLICT` for a `publishing` draft, which only exists via `COMMON_ERRORS`, not the procedure's `.errors(PHOTO_BAD_REQUEST)` call; this is fine (oRPC typed clients get `COMMON_ERRORS` on every procedure) but a future reader skimming only `.errors()` could miss it — not a web blocker.
