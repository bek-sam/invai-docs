# Review of T-6-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation + integrations-engineer on Opus
- Verdict: **escalate**

## Setup
Worktrees next to the repos, pinned at the reviewed SHAs (main repos have other wave-6 builders'
uncommitted work, so isolation matters): `invai-contracts-t65-review@3b8f390`,
`invai-backend-t65-review@5339a57` (excludes `03eff41`, other cards' NOT_IMPLEMENTED handlers),
`invai-web-t65-review@10e4a86` (includes `4c19a20`, `d0d89ce`, and the errors.ts grant, which had
already landed by the time I started). `node_modules` symlinked; own test DB `invai_test_t65`.

## Evidence I re-ran
| Command | Result |
|---|---|
| contracts: `tsc --noEmit` | clean |
| contracts: `biome check .` | clean, 46 files |
| contracts: `vitest run` | 31/31 pass |
| backend: `tsc --noEmit` | 11 pre-existing errors, all also present on `origin/main` (verified by archiving `origin/main` and running tsc there: 12 errors, same files/lines plus one T-6-5 itself fixed in `tenancy/service.ts`). None introduced by this card. |
| backend: `biome check .` | clean, 253 files |
| backend: `vitest run` | 488/492 pass. 4 fail in `src/api/authz.test.ts` on `production.sheets.markPrinting` (T-6-2's contract stub, no handler at this backend SHA). **Confirmed not a T-6-5 defect** but the premise "should pass in your worktree" no longer holds: I additionally checked out backend at `03eff41` (current HEAD, which does add NOT_IMPLEMENTED handlers for T-6-2/3/4) and the same 4 tests still fail there, now on `inventory.purchaseOrders.markPlaced` (T-6-1's stub) instead — i.e. contracts main has moved ahead of whichever backend commit you pin, for other cards' stubs, independent of T-6-5. Not blocking, but the card's "should pass" framing is stale by review time. |
| backend: `tsup` (build) | success |
| web: `tsc --noEmit` | clean |
| web: `biome check .` | clean, 137 files |
| web: `vitest run` | 76/76 pass |
| web: `vite build` | success |
| `scan-test-weakening.sh` (backend, base `711c37c`) | hits: mocks added (expected, spy setup) and 6 "removed" assertions — checked each: all are mechanical `getSupplierAdapter`/`sendMail` signature updates (added `await`, new required arg), same assertion re-added one line later in the same test. No weakening. |
| `scan-test-weakening.sh` (contracts, base `acbd294`) | no hits |
| `scan-test-weakening.sh` (web, base `7bf4b3d`) | 1 "removed" assertion, in `e2e/golden-path.spec.ts` — traced to `06e83e6`, a different card's fix, not in T-6-5's commits. Not applicable. |
| New-test-fails-on-old-code, backend `demo-guards.test.ts` vs `711c37c` | Fails (`clearSampleWorkspaceCache is not a function`) — real proof, not vacuous. |
| `grep -rn "Adapter(" src` (backend worktree) | every `carrierAdapter`/`carrierTracking`/`getChannelAdapter`/`getSupplierAdapter`/`billingProvider`/`sendMail` call site passes a scope/company/sender argument; `webhookAdapter` call sites (`sync.ts:668,825`) are typed verify/parse-only, no network method reachable; no low-level adapter (`shopifyAdapter`, `etsyAdapter`, `ssActivewearAdapter`, …) is called directly outside its owning factory file. |
| Curl on DB copy | not re-run (author's report shows it; unit + integration tests plus the code read give equivalent confidence for a token-budget-conscious round 1; will run if round 2 is needed). |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC1 (sample = `demoOwnerUserId IS NOT NULL` or retired marker; Desert Bloom real; regression test; golden path) | Yes | `demo-flag.ts` `isSampleRow`/`isSampleWorkspace`; `demo.ts:136-147` `retireDemoCompany` writes `settings.demoRetiredAt` before nulling the owner link; `demo-guards.test.ts:135-141,314-330` pins both directions (seeded shop real, sample/retired not); `org-hooks.ts:29-34` uses `isSampleRow`, not `companies.demo`; seed emails are real (`@desertbloom.test`, `vendor@suncitydtf.test`), unlike the demo's `.invalid` domain. |
| AC2 (nothing real for a sample workspace, every call site) | Yes for carrier, marketplace/channels, billing, mail. **Process gap for suppliers — see blocking finding.** | Grep of every `*Adapter(`/`billingProvider(`/`sendMail(` call site (above) shows a scope argument everywhere; `demo-guards.test.ts` proves it behaviorally with real+mock reference-equality and spy-call assertions (carrier, marketplace incl. a live-marked Shopify connection sync, billing, suppliers, email). |
| AC3 (test with fake real keys, spy/fetch-mock, covers every AC2 site) | Yes | `demo-guards.test.ts`, 10 tests, real EasyPost/Shopify/Stripe/S&S/nodemailer replaced by recording spies, env says real keys set; fails against pre-change code (verified). |
| AC4 (web shows DEMO_MODE) | Yes | `d0d89ce` adds `demo.cantPay` en+es and `isDemoModeError`/`demoModeMessage`; `10e4a86` wires it into `errorInfo()`. Web tsc/build/tests all clean with this in place. |

## Blocking findings
1. `invai-backend/src/integrations/suppliers/index.ts`, `src/modules/inventory/service.ts` (`supplierAdapterFor`, `listSuppliers`, `supplierStock`) — **out of owned paths and out of both documented grants** (the card's only two grants are `integrations/channels/index.ts` and `shipping/service.ts`+`shipping/jobs.ts`). The card's own AC2 says explicitly: "Blank suppliers are not in this AC at all... Raise this as a scope question (`scope-change-request`) rather than silently building it in." Both the plan-architect (`reviews/plan-architect-r1.md` line 38) and plan-PM (`reviews/plan-product-manager-r1.md` line 21) reviews independently flagged this and explicitly declined to fold it into T-6-5 unilaterally, directing it to the owner instead. I found no `scope-change-request`, no `owner-inbox.md` entry, and no `decisions/` record for this. The report doesn't mention filing one either. A real security gap was correctly identified and closed, but the process the card itself specifies was bypassed — this is exactly the "disagreement on scope" case the review skill routes to the tech lead/owner rather than a unilateral revert (reverting would reopen a real B-109-class hole: a sample workspace with its own S&S keys could place a real supplier order). **Escalating rather than blocking-and-reverting.**

## Checks
- [x] Only owned paths changed — **no**, see finding 1 (suppliers). The `ai/service.ts`, `channels/sync.ts`, `inventory/availability.ts` touches are also outside owned paths/documented grants, but each is a one-line mechanical pass-through of an argument the caller already had (`conn`), and this exact design ("check inside `getChannelAdapter`, cheaper than a grant into these three files") was explicitly recommended by the plan-architect review. I treat that as adequate pre-authorization in substance, though `wave.md`'s clarifications section was never updated to record it as a formal grant — a documentation gap, not blocking.
- [x] Nothing outside scope — no, per finding 1.
- [x] Tests exercise the behavior, none weakened (scan run in all 3 repos, all hits read and explained above)
- [x] Tenancy/idempotency/money/en+es — n/a for money (no new tenant tables); no idempotency concerns (all guard checks are read-only lookups); en/es present for the new user-facing string
- [x] Decisions recorded where needed — no, per finding 1; that's the crux of the escalation

## Optional notes (not blocking)
- `wave.md`'s "Clarifications from the plan review" section should be updated with an explicit grant line for `ai/service.ts`/`sync.ts`/`availability.ts`, matching what the architect review already recommended, so the paper trail is complete.
- The report's "known gaps" section is honest and specific (AI spend unguarded, token refresh not sample-guarded but spends nothing, `onboarding.ts` display-only) — all verified accurate by reading those files.
