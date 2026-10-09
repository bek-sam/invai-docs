# Wave 29: buyer text purge, two-step sign-in on the seeded shop, readable assistant answers, webhook imports, guard false positives

- Dates: 2026-10-09 →
- Goal (user outcome): a buyer's personalization text and any free-text note that may name them are gone on the same clocks as the rest of their data (S-56, due 2026-11-08); the seeded shop's owner and admin see the two-step sign-in rule like a real shop, and a failed lock email can't crash the API; the assistant's answers read as formatted text, not raw Markdown symbols; a shop that turned auto-import off gets no surprise orders from webhooks; agents stop losing turns to guard false positives.
- Owner order 2026-10-09: "push everything to 100%, go". This tech lead runs only wave 29.
- Scope ref: always in scope (security S-56 / compliance Amazon DPP: B-293, B-296; bugs: B-297, B-270, B-292; B-299 is a bug in wave 28's rule; B-298 is team tooling reliability).
- Fences: no deploys, no real keys, no outbound sends; gates run with AI keys blanked. Owner-pending items not touched: OI-3, 8, 13, 15, 17, 21, 25–32. At most 3 agents at once, reviewers included. No canary planted (OI-15 still open).
- Plan reviewed by: product-manager (2026-10-09, approve; decisions 0029 seeded shop follows the two-step rule, 0030 webhooks respect auto-import; `reviews/plan-pm.md`) and architect (2026-10-09, changes-required, 10 blocking card-text edits, applied as written: `purged` is visible in the contract, the sheet guard reads `order_items`, per-item clock, already-purged orders, missing fields and objects, storage-first order, T-29-2 paths and the stale-DB trap, AI-mode parsing, per-connection webhook skip and mock proof, guard allowlist; `reviews/plan-architect.md`). All edits were card text with exact wording supplied; no second plan round.
- Card change from the plan review: the contract step for `purged` became T-29-5 (architect, lands first). The guard card (B-298) moved out of this wave to stay at 5 cards; it is kept, with the architect's allowlist design, as `deferred-B-298-guard-false-positives.md` (the `T-29-5` in the plan reviews means that guard card).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-29-1](T-29-1-purge-buyer-text.md) Purge personalization text, rendered art and free-text notes on the 30-day and 18-month clocks (B-293, B-296, S-56) | backend-engineer (privacy) | opus | reviewer (fable) + security-reviewer (opus) + compliance-officer (sonnet) + architect (sonnet) | pii, tenancy, files, data deletion, floor-correctness | planned |
| [T-29-2](T-29-2-mfa-sample-rule-and-lock-email.md) Two-step rule uses `isSampleWorkspace`; lock email can't crash the API (B-299, B-297) | backend-foundation | opus | reviewer (fable) + security-reviewer (opus) | auth | planned |
| [T-29-3](T-29-3-assistant-markdown.md) Assistant answers render as safe formatted text (B-270); `artworkStatus.purged` label | web-engineer | sonnet | reviewer (opus) + security-reviewer (sonnet) | ui, untrusted AI output | planned |
| [T-29-4](T-29-4-webhooks-respect-auto-import.md) Webhooks don't create new orders while auto-import is off (B-292, decision 0030) | backend-engineer (channels) | sonnet | reviewer (opus) | import correctness | planned |
| [T-29-5](T-29-5-artwork-purged-contract.md) Contract: `purged` artwork status, 0.14.0 (lands first) | architect | sonnet | reviewer (opus) + backend-foundation (sonnet) + web-engineer (sonnet) | contract (additive) | planned |

## Order and slots (3 agents at once)
1. Plan review: product-manager and architect, in parallel (done).
2. Build slot A: T-29-5 (short, commits the contract first), T-29-1 (reads and plans until T-29-5 is committed), T-29-2. As each finishes, its reviews and then T-29-4 and T-29-3 take free slots.
3. Reviews as each card finishes; the gate when every card is approved.
- Ports and Valkey DBs: T-29-1 none (scripts on `invai_test` or a scratch DB, Valkey DB 12); T-29-2 API 3122, Valkey 13; T-29-4 API 3152, Valkey 14; T-29-3 the :3000/:5173 slot (the gate stack); T-29-5 none.

## Agreed interfaces
- T-29-5: `"purged"` appended to `ITEM_ARTWORK_STATUSES` and `ItemArtworkSummary.status`, contracts 0.14.0.
- T-29-1: `redactBuyerText(tx, orderIds, { scope: "shipped-items" | "all" })` in `modules/privacy/service.ts`, used by `redactOrders` (scope all) and the 30-day `purgeBuyerPii` (scope shipped-items). Storage first; an item whose object delete failed is left for the next night.
- T-29-1 floor rule: a purged item has `order_items.artwork_status = 'purged'` and null artwork keys, so the existing check at `production/sheets.ts:169` keeps it off every sheet; re-entry is `personalization.artwork.update`.
- T-29-2: `isMfaRequired` keeps its shape; `MfaMembership.demo` becomes `sample` computed with `isSampleRow`.

## Process notes
- QA acceptance tests first are skipped again (decision 0018 budget): every card except T-29-3 and T-29-4 has a security co-review that proves issues with failing tests, and the gate runs every suite. Recorded as a deviation.

## Integration gate
- [ ] Fresh reset, migrate, seed, AI keys blanked
- [ ] `run-golden-path` passes (API, browser, floor) and every touched repo's checks
- [ ] Key screens: not looked at by agents (decision 0024); the owner checks them from the feature test guide
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| | none planted (OI-15 open) | | | | |

## Log
- 2026-10-09 Fresh tech lead (memory read from the absolute path). State: all repos clean and pushed (contracts dc62328, backend 95324fe, web 4559618, floor 9304da1, ui 52af2b8, imaging f2d2eda, infra 1644dd4, docs 4122db1; imaging has an untracked `.DS_Store` only); nothing listening on 3000–3199, 5173, 5174, 8000; Docker healthy; 29 GB free. Cards written; plan review next.
- 2026-10-09 Plan reviews: PM approve (decisions 0029, 0030; docs c761694), architect changes-required (10 card-text edits; docs af629b4). Edits applied; contract step became T-29-5; guard card B-298 deferred.
- 2026-10-09 T-29-5 built (contracts 0f666f1, 0.14.0, 147 tests; web and floor typecheck clean; backend 2 expected errors in personalization/router.ts:30, fixed by T-29-1; report docs 1154d0f). Reviewer (opus) r1 started. T-29-1 (opus) and T-29-2 (opus, API 3122) building.
- 2026-10-09 T-29-5 reviewer r1 approve (docs 1958a72; new test fails on dc62328), backend-foundation r1 approve (ac74ba9; artwork_status is plain text, no migration). Web-engineer co-review waits for a slot. T-29-4 (backend-engineer channels, sonnet, API 3152, Valkey 14) started.
- 2026-10-09 T-29-4 built (backend 47ce0ee; 6 new tests, 3 red on main; full suite 1688 pass; real run on :3152: skip, re-send skip, manual sync imports once; PIDs 43118/43126/43133/43284/43292/43299/43300 stopped; dev DB keeps 2 mock orders 6200000001/2, settings restored). Reviewer (opus) r1 started.
- 2026-10-09 T-29-2 built (backend 384ef6f; docs fd3caf7 decision 0028 proposed; full suite 1688 pass; live :3122: owner@/admin@ required with deadline 2026-10-16T15:45Z, office@/vendor@ not; past-deadline 403 on a scratch copy; PIDs 42839/43043/43309 stopped; edited `src/api/context.ts`, outside the card list but in its role: reviewer judges). Reviewer (fable) r1 started.
- 2026-10-09 T-29-4 reviewer r1 changes-required (docs 11b7fcd): code right, but tests survive an always-skip mutation (known-order update test counts rows only; no Etsy cancel test). Round 2 (sonnet) fixes only the tests.
- 2026-10-09 T-29-1 built (backend 63682ed, 2529441; docs cb012d1 decision 0027 proposed, a6801bb report; full suite 1696 pass; 13 of 17 new tests red on main; scratch-DB run: delivered unit purged and its 3 objects 404, ready unit untouched, rerun all zeros). Departures: extra `failedFiles`; artwork keys deleted only under `{company}/artwork/` and only when no other item points at them. Gaps for backlog: gang sheet files (P1), legacy orphan renders, audit-log flags, manual uploads outside the artwork prefix. Reviewer (fable) r1 started.
- 2026-10-09 T-29-4 round 2 (backend 2872c59, tests only; always-skip mutation now turns 2 of 7 red). Reviewer r2 approve (docs 95b01bf). **T-29-4 approved.** T-29-3 (web-engineer, sonnet, :3000/:5173 slot) started.
- 2026-10-09 T-29-3 built (web 8d134d7; 181 tests incl. 9 new; build ok with `VITE_API_URL=` set; headless 390 px check on :3000/:5173 with the mock assistant: no img, no external link, no console error; ports freed). Reviewer (opus) r1 started.
- 2026-10-09 T-29-2 reviewer (fable) r1 approve (docs 8adde54; full suite 1697 pass; context.ts change judged necessary; live :3123 PID 45956 stopped). Security co-review (opus) started.
- 2026-10-09 T-29-1 reviewer (fable) r1 approve (docs 6d2de7d; 54 tests on invai_test + MinIO; 13/17 red on main; mutations on item-state, clock and failed-delete filters go red; withTenant->withSystem survives, non-blocking). Security co-review (opus) started; compliance and architect after.
- 2026-10-09 T-29-3 reviewer (opus) r1 approve (docs f41c495; 4 of 9 new tests red on base; isSafeAppPath fuzzed with 24 inputs; build env need is pre-existing, CSP guard since T-23-1). Security co-review (sonnet) started.
- 2026-10-09 T-29-3 security (sonnet) r1 approve (docs 9ee8be6; 22 hostile answers give no image or external link; prod CSP `img-src https:` does not block images, so the parser drop is the only control: follow-up test + optional CSP narrowing to backlog). **T-29-3 approved.** T-29-5 web-engineer co-review started.
- 2026-10-09 T-29-5 web-engineer r1 approve (docs eb8e65b; web and floor typecheck clean; `purged` has en/es label, neutral badge, filter count fallback). **T-29-5 approved.** T-29-1 compliance co-review (sonnet) started.
- 2026-10-09 T-29-1 compliance (sonnet) r1 approve (docs 26f08df; 0027 compliance-accepted; gang sheet files and pre-T-29-1 orphan renders keep the DPP 30-day row Partial; manual-upload gap to add to 0027 known gaps). Architect co-review (sonnet) started.
- 2026-10-09 T-29-2 security (opus) r1 approve (docs fbc4119; 0028 accepted; regression tests in its own security suite, backend 246838f). **T-29-2 approved.** Security found `pnpm typecheck` red at HEAD from T-29-4 r2 (`webhook-auto-import.test.ts:205`, TS2322; the r2 review re-ran vitest only). Handled as a gate fix (not a third review round): owner fixes types in the test only, then one reviewer pass over that fix and 246838f.
- 2026-10-09 T-29-1 architect (sonnet) r1 approve (docs 5d338a0; design matches plan items 1-6; both departures accepted). Waiting on T-29-1 security.
- 2026-10-09 Gate fix: backend 7a763a5 (T-29-4 test types narrowed). Reviewer pass approve on 7a763a5 and 246838f (docs 237c317; mutations prove both new security tests). Waiting on T-29-1 security.
- 2026-10-09 T-29-1 security (opus) r1 approve (backend 32113d7 own test file: cross-company keys survive + S-59 `it.fails`; docs f3007a1: S-56 Fixed, 0027 accepted). New S-59 (Low): a reused buyer-photo key is deleted without a shared-use check. **T-29-1 approved. Every wave 29 card is approved** (each required reviewer's latest file says approve). Gate started.
