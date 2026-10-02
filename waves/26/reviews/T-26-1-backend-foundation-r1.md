# Review of T-26-1 (round 1)

- Reviewer: backend-foundation on sonnet
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-contracts && pnpm typecheck` | `tsc --noEmit` clean |
| `cd invai-contracts && pnpm test` | 12 files, 143 tests passed |
| `cd invai-backend && pnpm typecheck` | clean (0 errors; confirms T-26-3/T-26-4 landed the two fixes T-26-1's report flagged as expected) |

## Acceptance criteria (backend-implementability lens only; full criteria owned by `reviewer`)
| # | Met? | Evidence |
|---|---|---|
| Permissions exist and are refused for the right roles | yes | `src/roles.ts`: `photos.read`/`photos.manage` added to `PERMISSIONS`, granted to `OFFICE`, `DESIGNER` explicitly; `owner`/`admin` inherit via `SHOP_ALL`/`SHOP_ALL.filter(OWNER_ONLY)` — no new OWNER_ONLY entry, so admin gets both too. Presser/packer/receiver/vendor arrays untouched → refused. |
| Error shapes fit backend's error mapping | yes | `PHOTO_BAD_REQUEST` (400, closed reason enum + nullable count), `IMAGE_CAP_ERRORS.IMAGE_DAILY_CAP_REACHED` (429), reused `CREDIT_ERRORS`/`SPEND_CAP_ERRORS` (now exported from `contract/ai.ts`, additive — nothing else imports the old unexported bindings) |
| Rate buckets specified and matched by backend | yes | ADR §8 names every procedure's method/bucket; T-26-4's `AI_BUCKET_PROCEDURES` set and `NON_GET_READS` entry match exactly; `buckets.test.ts` asserts all three `ai`-bucket procedures, `estimate`→reads, `reviewImages`→writes |
| Outbox/realtime event names fit the existing registries | yes | `Events["photo_set.created"/"completed"]` (`src/events.ts`), `RealtimeEvents["photo_set.updated"]` (`src/realtime.ts`), both appended at the end, matching `src/modules/photos/jobs.ts`'s `onEvent("photo_set.created", dispatchSetJob, ...)` and `service.ts`'s `publishSet` usage I inspected in T-26-4 |
| Additive only | yes | No procedure/field/enum removed or renamed; `ListingDraft.imageDisclosures` optional; `CREDIT_KINDS` appended at the end (`photo_image`, `photo_scene`); `PHOTO_VIEWS`/`PHOTO_CHECK_CODES` append phase-B values last; `p5-reasons.test.ts`/`digest.test.ts` pins relaxed to "present/in order" rather than "exact last element", which is the established convention for a widened enum (precedent: T-22-1 review) |
| CREDIT_KINDS backend mirror | yes | `invai-backend/src/db/schema/ai.ts` (T-26-3, `d7e7b6c`) mirrors `photo_image`/`photo_scene` at the same position; `service.ts:1476` `inArray` error from T-26-1's report is gone in the current backend typecheck |

## Blocking findings
none.

## Checks
- [x] Only owned paths changed (`invai-contracts/src/**`, ADR + index row) — `git show --stat` confirms
- [x] Nothing outside scope
- [x] Tests exercise the behavior; no weakening (relaxed pins are a widened-enum convention, not a loosened assertion of new behavior)
- [x] Tenancy n/a (contract-only); idempotency key present on `createSet`; money never appears (checked: no `Cents` import in `schemas/photos.ts`); en/es n/a (contract-only, no UI strings)
- [x] Decisions recorded: ADR 0023 covers design lock, disclosures, approval, credits, queue, retention, rate buckets

## Optional notes (not blocking)
- README namespace table / permission-model section not updated (author flagged this gap themselves; `README.md` is outside `src/**` so technically outside owned paths — a one-line follow-up card is enough, not a reason to hold this card).
