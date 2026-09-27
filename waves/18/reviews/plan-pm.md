# Wave 18 plan review: product-manager (scope)

- Reviewer: product-manager, 2026-09-27. Inputs: `wave.md`, T-18-1..T-18-5, `product/scope.md` (item 16, `#market-and-digest-fences`), `specs/market-signals.md` (AC1–AC33), `reviews/plan-architect.md` (approve-with-changes, all 8 applied).
- **Verdict: approve.**

## Scope check
- All 5 cards sit inside item 16 (`market-signals`); none touches item 17 (weekly digest). T-18-3's `listDigestMarketItems` is a read-only service export for wave 19 to call later — no digest procedure, job, template or email ships here. Acceptable prep, not scope creep.
- Every hard fence carried into `wave.md` word-for-word: no scraping, no cross-shop use, no auto price/listing/ad/PO writes, no Etsy competitor data, no real paid source without the owner, no forecasting model. Confirmed against `scope.md#market-and-digest-fences`.
- Census real (keyless) call in T-18-2 AC2 matches the spec's explicit "real, no spend" design (not a new paid source/account) — no extra owner sign-off needed beyond OI-6/decision 0014.
- Wave is 5 cards. Good.

## Mock visibility rule and "Sample data" wording
- Matches what I wrote in `scope.md` line 48 and the spec's "Providers and mocks" section: sample-workspace test is `isSampleWorkspace(companyId)`, explicitly **not** `companies.demo` (seeded Desert Bloom has `demo=true` and must get real behavior). Verified in T-18-2 AC3 and T-18-3 AC2a.
- `wave.md`'s formula adds `|| env.allowMocks`. Checked `invai-backend/src/env.ts:193` — this is the existing `ALLOW_MOCKS` flag, not new; it's ops-controlled, not shop-controlled, so it doesn't weaken the "never reaches a real shop in production" fence. No change needed, but the ADR (T-18-1 AC6) should say in one line that `allowMocks` is an existing ops override, not a new bypass, so a future reader doesn't mistake it for scope drift.
- "Sample data" in the recommendation's own text (not just the badge) is carried through: T-18-3 AC2a/AC30, T-18-4 AC3a, T-18-5 AC3 — matches `rec.sample` copy and my fence wording.

## AC coverage (AC1–AC33 → card AC / test)
| AC | Home | AC | Home | AC | Home |
|---|---|---|---|---|---|
| 1 | T-18-3 AC2 | 12 | T-18-3 AC3; T-18-4 AC6 | 23 | T-18-1 AC6; T-18-3 AC1 |
| 2 | T-18-4 AC2; T-18-5 AC1 | 13 | T-18-2 AC7; T-18-4 AC9 (eval) | 24 | T-18-1 AC2; T-18-3 AC12 |
| 3 | T-18-3 AC5, AC7 | 14 | T-18-4 AC5, AC9 (eval) | 25 | T-18-3 AC3 |
| 4 | T-18-3 AC7, AC8 | 15 | T-18-4 AC2; T-18-5 AC7 | 26 | T-18-3 AC11 |
| 5 | T-18-3 AC8 | 16 | T-18-3 AC13; T-18-4 AC7 | 27 | T-18-3 AC11; T-18-1 AC3 |
| 6 | T-18-3 AC9; T-18-4 AC1 | 17 | T-18-3 AC4 | 28 | QA separate scale run (spec footnote); T-18-3 AC15 budget check |
| 7 | T-18-3 AC5; T-18-4 AC1 | 18 | T-18-3 AC4, AC7; QA 2nd-pass acceptance test | 29 | T-18-3 AC2a |
| 8 | T-18-3 AC6; T-18-4 AC2 | 19 | T-18-3 AC5 | 30 | T-18-3 AC2a; T-18-4 AC3a; T-18-5 AC3 |
| 9 | T-18-3 AC7 | 20 | T-18-2 AC5; T-18-3 AC10 | 31 | T-18-4 AC3a |
| 10 | T-18-3 AC6 | 21 | T-18-3 AC3; T-18-4 AC4 | 32 | T-18-3 AC12; T-18-5 AC5 |
| 11 | T-18-4 AC2, AC9 (eval) | 22 | T-18-2 AC3 | 33 | T-18-1 AC3; T-18-4 AC3; T-18-5 AC4 |

No AC without a home.

## Required changes
None blocking. One suggestion (non-blocking): T-18-1's ADR 0015 notes `env.allowMocks` as the existing ops flag it is, per above.

## Notes
- Permission matrix (`niches.set` → new `market.niches.manage` for owner/admin/office/designer; recommendations on `finance.read`, designer refused) matches the spec's Users section exactly.
- Niche taxonomy (69 niches, PM-owned `product/market-niches.md`) is read-only to T-18-3 as required.
- Open question 4 (Shopify §2.3.24 ML-tuning question) doesn't block this wave — calibration is a later, manual PM decision (spec Step 7.4), not built here.
