# Review of T-26-1 (round 1)

- Reviewer: reviewer on opus
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| contracts `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` (node v24.21) | tsc 0; biome 64 files, no fixes; 12 files, 143 tests passed |
| `pnpm typecheck` in invai-backend (HEAD e32f9c5, after T-26-3/T-26-4), invai-web, invai-floor | exit 0 / 0 / 0, 0 `error TS` each (the 2 backend errors in the report are gone) |
| `scan-test-weakening.sh invai-contracts 9026680~1` | 3 removed assertions (below), no skip/only/mock/snapshot/config hits; `toBeTruthy` hit at photos.test.ts:405 is a new event-parse check, not a loosening |
| Read `@orpc/contract` `validateORPCError` (installed dist) | a BAD_REQUEST whose data fails the declared schema passes through as `defined:false`, never a 500 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `contract/photos.ts:70-163`: 10 procedures, each `proc(permission)` + Zod in/out; base supplies NOT_FOUND/CONFLICT/FORBIDDEN; CREDITS_EXHAUSTED, AI_SPEND_CAP_REACHED, BAD_REQUEST (`{reason, count}`), IMAGE_DAILY_CAP_REACHED (429) on createSet; photos.test.ts:163-213 asserts routes, permissions, error maps |
| 2 | yes | Diff removes nothing; enums appended at tails (CREDIT_KINDS, PERMISSIONS, RealtimeEvents, Events); `ListingDraft.imageDisclosures` optional; `CREDIT_ERRORS`/`SPEND_CAP_ERRORS` only gain `export`. All three consumers typecheck green. Consumer sweep listed in the report |
| 3 | yes | No `Cents` in photos schemas; every credit field `int().nonnegative()`; `HexColor` `^#[0-9a-fA-F]{6}$`; only pixel sizes (no inch fields); ratios via `Ratio` |
| 4 | yes | ADR 0023 §1 design lock, §2 two-check drift (outline ring, restored print box, SSIM, upscale), §3 disclosures (Etsy flag, XMP synthetic performer, templates no AI), `image_disclosures` column, §4 approval + CSV has no image URLs, §5 credits per composition, §6 queue, §7 productRef, §8 method + bucket table, §9 retention; index row README:36 |
| 5 | yes | Green above; rejections tested: `#111`/`111111`/`#11111g`, garment `polo`, empty garments, `lifestyle` as template view, `csv` channel |

Phase B shapes present: `lifestyle` (PHOTO_VIEWS tail, `LifestyleRequest`), `design_drift`/`region_changed`, `pushTargets`, `pushToShopify` with `productRef: {listingId}`, `IMAGE_DAILY_CAP_REACHED`. Version 0.12.0 in package.json and compat.ts (compat.test holds equality).

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `src/**` plus `package.json` version bump (required by compat.test; architect owns `invai-contracts/**`); docs: ADR + index row + report
- [x] Nothing outside scope
- [x] No weakened tests: the 3 relaxed pins (digest.test.ts realtime/CREDIT_KINDS `.at(-1)`, p5-reasons version) are legitimate: the exact tail and version moved to photos.test.ts:230, :418, :432, and digest_narrative keeps an order check vs market_niche. Same convention as earlier waves
- [x] Tenancy/idempotency: contract-only; `idempotencyKey` (8-128) on createSet and pushToShopify; no money; en/es n/a (no UI strings)
- [x] Decisions recorded (ADR 0023)

## Optional notes (not blocking)
- README namespace/permission rows missing (README outside the card's `src/**`). Docs drift only, no consumer impact: tech lead to add it to a follow-up or grant the path. Does not block.
- photos BAD_REQUEST redefines the code with required `data`; oRPC input-validation errors (`data.issues`) arrive `defined:false`. Web (T-26-5) must treat a missing `data.reason` as a generic invalid-input message.
- `DesignPhotoAnalysisResult.failed.error` and `PhotoImage.error` are free English strings; web should map known codes, not show them raw.
- Card text said `sceneIds`; the contract uses `sceneKinds` (author's shape choice, consistent with `PhotoSceneKind`).
