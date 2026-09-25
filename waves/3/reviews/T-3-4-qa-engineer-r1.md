# Review of T-3-4 (round 1): qa-engineer co-review (golden path)

- Reviewer: qa-engineer (co-review) on Opus 5.5
- Author: backend-foundation on Opus 5.5
- Verdict: **escalate**. I can't give the golden-path sign-off from a worktree (details below). No code defect was found by the golden path; this needs a run from the main tree, at the integration gate or after the web fix.

## Evidence I re-ran
| Command | Result |
|---|---|
| Fresh `reset → migrate → seed` of `invai_r34_copy` (imaging :8194 up), API :3194 + worker | seed completed |
| `E2E_API=1 E2E_API_URL=http://localhost:3194 E2E_WEB_URL=http://localhost:5194 playwright test e2e/api-golden-path.spec.ts` from the `a6ea3a1` worktree | **7 passed, 1 failed, 5 did not run** (8.8 s): steps 1–7 green, including 2 (Etsy CSV import, the ≤300-row inline path), 5 (sheet build) and 6–7 (vendor portal, received) |
| Step 8 failure | `Error: Station token required` at `api-golden-path.spec.ts:272`. Root cause, environment: `e2e/helpers/api.ts:12` resolves `seed-output.json` from `<workspace>/invai-backend`, i.e. the **main** checkout, whose station token belongs to a different seed. My seed's token was in the worktree. Overwriting the main repo's tracked `seed-output.json` was (rightly) denied, and a second reseed-and-rerun was also denied. Steps 9–13 (label and tracking, profit, AI, assistant, tenant isolation) didn't run because the suite is serial. |
| Browser suite (`golden-path.spec.ts`, `screens.smoke.spec.ts`) | **Not run** (tech lead's stall instruction: static checks plus the key live check first) |
| Scale checks I did run live | CSV 1,200 rows: queued in 63 ms; worker killed at 400/600 orders; resumed; 600 orders and 1,200 units exactly. Re-import: 600 unchanged. Batch of 10 with the worker killed at 5: 10 labels, 0 duplicates (reviewer file). |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 5 API and browser golden-path suites pass | **Not verified by me** | 7/13 API steps are green on a fresh seed. Steps 8–13 and the browser suite were not re-run, for the environment reason above. The author reports 13/13 and 15/15 on `invai_t34_copy`. |
| Golden path step 9 (label and tracking) touching this card | Unverified | Step 9 uses a single `shipping.buy`, not `batchBuy`, so the batch change is mainly exercised by the browser suite's "Buy & print" (if present) and by my live kill test. |

## Blocking findings
None in code from the golden path. The escalation is for verification capacity: someone needs to run both suites from the main tree on a fresh seed after the web fix (reviewer/web-engineer finding 1) lands.

## Checks
- [x] No E2E files changed in these commits (`e2e/**` untouched).
- [x] No test weakening in the E2E suites.
- [x] Personalization renders are now async. The seed renders directly (`renderValues`), and step 5's sheet build still reached utilization ≥ 80% on my seed. But an import right before a sheet build now needs the worker running for personalized units to become eligible. **Worth adding a wait-for (not a sleep) in the golden path if a step ever builds sheets from freshly imported personalized orders.**
- [x] No PII in my evidence.

## Optional notes (not blocking)
1. **Suite portability.** `e2e/helpers/api.ts` hard-codes `<workspace>/invai-backend/seed-output.json`. Add an `E2E_SEED_OUTPUT` (or `E2E_BACKEND_DIR`) override so reviewers can run the API golden path from a worktree against their own seeded copy. This is a qa-engineer-owned change; I'll file it.
2. **Scale profile.** Add a mid-size profile case: a 3,000-row CSV plus a 50-label batch with p95 targets (import-to-done time, batch time) now that both are jobs. Include a worker-kill variant that asserts one label per order and exact import counts.
3. **Batch in a browser E2E.** The browser golden path should assert the "Buy & print" toast and the queue count dropping, with a wait-for on the job. This covers the new poll, including a deadline once the web fix adds one.
