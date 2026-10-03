# Review of T-27-3 (round 1)

- Reviewer: security-reviewer on opus
- Author: backend-engineer on opus
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/modules/photos src/db/rls-coverage.test.ts src/api/authz.test.ts` | 7 files, 74 passed, exit 0 |
| S-55 proof in `src/modules/photos/security.test.ts` without the `it.fails` marker | fails: `expected [ {…} ] to have a length of 2 but got 1` (2 paid calls, 1 recorded); with marker 6 passed + 1 expected fail; `pnpm typecheck` clean |
| Read 0041 migration, scenes.ts, push.ts, purge.ts, jobs.ts diff; diff scan for skip/only/fails | `photo_pushes` RLS + tenant policy, (company_id, set_id) composite FK; no weakened tests |

## Acceptance criteria (security view)
| # | Met? | Evidence |
|---|---|---|
| 1, 8 | yes | `sceneRefusal` under `lockCompanyCharges` before any provider call (claim and attempt 2); claimed scenes count as pending, so caps are effectively reserved; per-shop fan-out bounded by that count |
| 2 | no | regenerate-once and uncharged second drift OK; one `photo_scene` charge guarded by `chargedAt` under the lock; but a retry after an upload failure pays the provider twice and records one call (S-55) |
| 4 | yes | connection via `getConnectionRow` and listing by id under RLS (foreign → NOT_FOUND), listing must be on the same connection + shopify; approved + company-key images only; presign 6 h (`PUSH_URL_TTL_S`); idempotency row + request hash (CONFLICT on reuse); audit row per push; status guard on reruns |
| egress | yes | only blank base + mask (imaging, company-prefixed keys checked with `isCompanyKey`) and the fixed-vocabulary prompt reach the provider; design pixels never leave |
| retention | yes | `purgePhotoFiles` reads ids/keys `withSystem` (reason comment), deletes only `isCompanyKey` keys, writes per tenant in `withTenant`; logs carry ids, no PII |

## Blocking findings
1. `invai-backend/src/modules/photos/scenes.ts:356-357` — `putObject` runs before `recordImageGen`. Scenario: OpenAI returns a billed scene, S3 answers 503, the job retries, OpenAI is billed again; the first call is never on the spend counters or the shop cap (S-55, Medium, same class as S-53). Fix: record the result right after `generateScene`, before the upload; flip the S-55 test to `it`. Due 2026-11-02.

## Checks
- [x] Only owned paths changed (photos module, schema photos.ts, 0041, imaging client additions)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy (`withTenant`, RLS on `photo_pushes`), push idempotency, money in cents
- [x] Decisions: ADR 0023 followed

## Optional notes (not blocking)
- `sizePx` not passed to `recordImageGen` on the failure path (primary noted); harmless at 1024 today, pass `SCENE_SIZE_PX` when sizes vary.
- Purge selects by composition `createdAt`, not by scene completion: a scene job still retrying after 7 days would lose its base. Low; consider `scene_key is not null` or images closed.
