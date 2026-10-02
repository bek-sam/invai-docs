# Review of T-26-4 (round 1), security co-review, flags tenancy, files, payments (credits)

- Reviewer: security-reviewer on opus
- Author: backend-engineer on opus
- Verdict: changes-required (1 Medium: S-51)

## Evidence I re-ran
| Command | Result |
|---|---|
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/modules/photos src/lib/security.test.ts src/modules/tenancy/security.test.ts src/api/authz.test.ts src/db/rls-coverage.test.ts src/api/buckets.test.ts` | exit 0; 9 files, 72 passed, 1 expected fail (S-51 marker) |
| new `src/modules/photos/security.test.ts` (mine), credit test as plain `it` | `expected -8 to be greater than or equal to 0` (S-51) |
| same file: B calls analyzeDesign/estimate/getSet/reviewImages/exportZip/attachToDraft with A's ids | NOT_FOUND on all 6; B's set + A's image ids → BAD_REQUEST; A's images unchanged; A's set not in B's list |
| same file: presser, packer, receiver on all 8 live procedures | FORBIDDEN x24 (vendor/floor/anon: `authz.test.ts` green) |
| `grep withSystem src/modules/photos` | none; jobs enter `withTenant(companyId)` from the outbox event / job input |
| `drizzle/0040_photos_sets.sql` | 4 tables, RLS enabled x4, `_tenant` policy x4, composite `(company_id, id)` FKs to designs/sets/compositions |
| `scan-test-weakening.sh invai-backend 30618a0~1` | hits only in T-26-3 eval/mock files and my own new test |
| Live API curl | not run; router-level calls above go through the real guard against `invai_test` |

## Acceptance criteria (security part)
| # | Met? | Evidence |
|---|---|---|
| 1 RLS, unique keys | Yes | migration; rls-coverage green |
| 2, 7 foreign design/draft → NOT_FOUND | Yes | tests above; `getDesign`/`getDraft` tenant-scoped |
| 3 credits refused before rows | Yes, but not reserved | S-51 |
| 4 charge once (FOR UPDATE + `charged_at`) | Yes | `recordRenders` locks set then composition; run-twice test in `photos.test.ts` |
| 6, 8 out_key server-built under `<company>/photos/<set>/`; presign only `isCompanyKey`; zip only approved images of this set | Yes | `service.ts:1123`, `:912`, `:181`, `:894-902`; stored render key re-checked `:1175` |
| Rate bucket | Yes | analyzeDesign/createSet/pushToShopify → `ai`; buckets.test green |
| No buyer PII to prompts/logs | Yes | prompt gets design name, tags, preview key, palette; logs carry ids only |

## Blocking findings
1. `src/modules/photos/service.ts:533` + `:1194` (S-51, Medium, payments integrity): `createSet` asserts the balance but reserves nothing and the render charge never re-checks, so a shop with 8 credits creates two (or 20/min) 8-composition sets and all render; balance ends at -8 (proof above). Wave 27 scenes (10 credits + real image-provider spend) reuse this path. Fix: subtract uncharged compositions of open sets before the assert, and in the render claim step fail a composition with "AI credits are used up" when the balance is below its cost; flip my `it.fails` to `it`. Owner backend-engineer, due 2026-11-01, before any scene charge.

## Checks
- [x] Only owned paths changed (grant lines as granted)
- [x] Nothing outside scope (security view)
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy: `withTenant` on every handler and job, RLS + composite FKs, no `withSystem`
- [x] Decisions: none needed; S-51 recorded in `security/v1-review.md`

## Optional notes (not blocking)
- Low: `exportZip` (writes bucket, 120/min) queues a new zip each time `channel` toggles (bounded by S-50 caps); `attachToDraft` accepts another design's draft of the same shop (author's gap).
