# Review of T-18-4 (round 1)

- Reviewer: reviewer on sonnet
- Author: ai-engineer on opus
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-rev-t18-4 987b839` | clean worktree at the card's last commit |
| `tsc --noEmit` (invai-backend-rev-t18-4) | clean, no errors |
| `biome check .` | `Checked 339 files … No fixes applied.` |
| `vitest run src/ai src/modules/ai/{assistant-tools,niche,service,market.acceptance}.test.ts` (own DB `invai_t18_rev_4`, Redis DB 10) | `market.acceptance.test.ts`: 2 failed (AC30, AC33), 1 suite-level throw ("no mock niche series is rising or falling"), rest green; all of T-18-4's own test files green |
| Full `vitest run` (same DB) | `2 test files failed, 110 passed (112) — 8 failed, 877 passed, 3 skipped (888)`. Failures: 2 in `src/modules/ai/market.acceptance.test.ts` (AC30, AC33) + 6 in `src/modules/market/market.acceptance.test.ts` (AC3, AC17, AC19, AC26, AC27, AC30-backend). Every failure traces to T-18-2's mock comparables (<8) and mock seasonal shapes not peaking, both already routed in `wave.md` "Cross-card findings routed" / "QA findings routed" to T-18-2/T-18-3. None are in a T-18-4-owned file (`assistant-tools.test.ts`, `niche.test.ts`, `service.test.ts`, `answer.test.ts`, `answer-guard.test.ts` all green) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | Only one real removed assertion pair (`ASSISTANT_PROMPT.version).toBe(4)` / "Never cite outside market facts"), replaced by an equivalent assertion at `service.test.ts:654` (`toBe(5)`) and the updated rule text — not a weakening. No `.skip`/`.only`, no mocks of the unit under test, no loosened config |
| `tsx evals/market/main.ts` against a fresh migrated copy (`invai_t18_rev_4_dev`, `createdb -T invai`, then `db:migrate`) | `Overall plumbing: 15/21 (71%)`, failures: mk-003, mk-004, mk-013, mk-018 ("mock data without 'Sample data'") + mk-005, mk-006 (October peak, the known T-18-2 issue). The first four are a **new, reproducible finding** below (author's baseline reported 19/21 with only mk-005/006 failing) |
| Live probe of `runAssistant` on an eval-seeded shop, `get_price_position`/`simulate_price` for a design with mock Amazon comparables (script deleted after use) | `outcome: "fallback", secondIssues: ["missing_sample_label"]`; final text shown to the user has no "Sample data"/"sample data" anywhere — see Blocking finding 1 |
| API on port 3172 against a migrated copy of the dev DB (`invai_t18_rev_4_dev`), T-18-3's jobs run (`refreshDemand`, `refreshPricing`, `computeSignals`: 40 designs, 639 signals, 18 recs) | 3 starters + 1 Spanish exercised (below) |
| Refused case: `designer@desertbloom.test` → `POST /api/v1/ai/assistant/ask` | `403 FORBIDDEN "Missing permission ai.assistant.ask for ai.assistant.ask"` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Tools per spec table, Etsy `available:false`+reason, `insufficient`+reason, ≤8 prices | yes | `assistant-tools.test.ts` green; live: Amazon (csv_only) → "isn't connected"; `prices:[1..9]` rejects (test) |
| 2 Answer honesty (numbers from tools, regenerate once then fall back, source+date, sample data, band, thin, disagreement, no sellers, no promises, language) | **partially** | `answer.test.ts`/`answer-guard.test.ts` green for the cases they cover, and the mechanism works correctly for `get_market_trend`/`get_seasonality`. But the fallback path itself violates the "sample data" rule for `get_price_position`'s insufficient-comparables branch and for `simulate_price` whenever their `mock`/`sources` carry a mock flag — see Blocking finding 1. No unit test in `assistant-tools.test.ts` exercises `simulate_price` or the unavailable branch of `get_price_position` with `mock: true`, which is why this slipped through |
| 3 Recommendations on stream + stored + recorded once + reload | yes | `service.test.ts`; live: 3 R1 ids on `tool_result`, `getConversation` returned them after reload |
| 3a Sample-data text; trademark fixed answer | yes for `get_market_trend`/`get_seasonality`; **no** for `get_price_position`/`simulate_price` in the case above | live probe + eval mk-003/004/013/018 |
| 4 Niche route (Haiku, JSON, taxonomy check, credits, mock) | yes | `niche.test.ts`; credit kind charged as `sku_suggestion` pending the architect's contract follow-up (documented, tracked in `wave.md`) |
| 5 Injection in tags only as data | yes | `answer.test.ts` AC14 (900% tag rejected); eval mk-014/015 pass |
| 6 `screenMarketTerms` drops ≥ threshold, counter | yes | `niche.test.ts` AC12; threshold 60 (the existing `assertTrademarkGate` "high" cutoff) documented and measured against the 69-niche taxonomy (438 labels), no false positive on St. Patrick's Day etc., exact marks (Disney) still caught at 70–85 |
| 7 Read-only | yes | `assistant-tools.test.ts` AC16 (row-count snapshot unchanged, `recordRecommendationsShown` not called from a tool) |
| 8 Mock routing (+ wave 17) | yes | `assistant-tools.test.ts` AC8 |
| 9 Evals ≥16 cases, mock mode, baseline | yes (21 cases) but baseline is stale | baseline.json claims 19/21; my rerun on a fresh copy gets 15/21 (see finding 1) |
| 10 Tenant isolation; existing assistant tests pass | yes | `assistant-tools.test.ts` AC10 (company B's design id → `not_found`, never read); T-17-3 tests green after `74268c3`; full suite confirms no T-18-4 regression |

## Blocking findings

1. **`invai-backend/src/modules/ai/assistant-tools.ts:1583-1591` (`get_price_position`, unavailable branch) and `:1698-1702` (`simulate_price`) — the fixed, code-written `answer` never discloses a mock source, even though `meta.mock` can be `true`, so the gateway's own fail-closed fallback still violates the "sample data" guardrail (AC2, AC3a/AC30, spec Step 6.3).**

   `get_market_trend` (`sourceLine`-based `src` in its template) and the *available* branch of `get_price_position` (`assistant-tools.ts:1587`, `const src = base.sources.map(...)`) both fold each source's mock flag into the answer text via `sourceLine()`, which appends "(Sample data)"/"(Datos de muestra)" per mock source. The *unavailable* branch of `get_price_position` and all of `simulate_price` build their `answer` without ever calling `sourceLine`/using `src`, yet both still set `base.mock`/`meta.mock` from `p.mock` / `s.mock`, which is `true` whenever a mock Amazon/Walmart comparables source contributed (`market/service.ts` `getPricePosition`/`simulatePrice`, `sources: [own, ...comparables.sources]`).

   Reproduced end-to-end on `987b839` with the real gateway (`runAssistant`), an eval-seeded shop, and the question "What margin would I get if I priced my Amazon shirt higher?" on a design whose mock Amazon comparables are 6 (below the 8-comparable minimum, `amazon_pricing` source, `mock: true`):
   ```
   tool_result get_price_position: {"mock":true,"sources":[{"source":"amazon_pricing", ...,"mock":true}]}
   [ai.gateway] assistant answer failed the check {"outcome":"fallback","firstIssues":["missing_sample_label"],"secondIssues":["missing_sample_label"]}
   final text: "Here is what your data shows (straight from the tools): **Retro Camping Bear, Amazon**:
     I need at least 8 comparable listings on Amazon to place your price, and there are fewer.
     **Retro Camping Bear, Amazon** (your 90-day costs): $0.10: net -$8.80 per unit, ... "
   ```
   The second pass (the tools' own guaranteed-safe fallback text, `fallbackAnswer()` in `src/ai/validators/answer.ts:189`) is what the user actually receives, and it *still* fails `validateAnswer`'s own "sample data" rule (`answer.ts:139-146`) — the guardrail's fail-closed design assumes the fallback always passes its own check, but for these two tools it structurally cannot. This is not a mock/model quirk: `assistant-tools.test.ts:1321` ("simulate_price: at most 8 candidate prices...") is the only unit test that inspects `simulate_price`'s answer text, and it stubs `mock: false, sources: [prov("own", false)]`, so the `mock: true` path was never exercised in a unit test. The same gap reproduces deterministically in `evals/market/main.ts` against a fresh migrated DB copy: cases mk-003, mk-004, mk-013, mk-018 (all tagged `deterministic: true`) fail with `"mock data without 'Sample data'"`, whereas the committed `evals/baseline.json` (from `987b839`) records only mk-005/mk-006 failing (19/21) — the baseline is stale/inaccurate for this reason, not only for the T-18-2 October-peak issue.

   Failure scenario: a mid-size pilot shop connects Amazon (a real, non-mock connection status) and asks "Am I priced right on Amazon?" or "What margin would I get if I raised my price?" before it has 8 tracked comparables (the common case per the routed T-18-2 comparables-count bug, and also possible later at n=6-7 even after that bug is fixed). The assistant answers with specific dollar/percent figures built in part from a mock Amazon pricing source, with no "Sample data" disclosure anywhere — the exact harm Step 6.3/AC30 exists to prevent ("a real owner could spend on designs or change a price on a fabricated trend... a badge alone is too little friction", spec "Providers and mocks").

   Fix direction (for the author, not prescribed): give `simulate_price`'s answer template a `sourceLine`-based disclosure when `s.mock` (mirroring `get_price_position`'s available branch), and give `get_price_position`'s unavailable branch the same treatment when `p.mock` is true; add a unit test for each with `mock: true` sources and no recommendation, and refresh `evals/baseline.json` after the fix (the 100%-comparables-count part of mk-005/006/AC30-backend/AC33 remains T-18-2/T-18-3's, already routed).

## Checks
- [x] Only owned paths changed (`git diff --stat` across the 8 commits: `assistant-tools.ts`+test, `niche.ts`+test, `service.ts`+test (scoped to the granted hunks — confirmed `74268c3` touches only the `USER_FIRST` tie-break inside `ask()`/`getConversation`, matching the retroactive grant), `src/ai/**`, `evals/assistant/**` (none changed), `evals/market/**`, `evals/baseline.json`, `src/db/schema/ai.ts` (grant, `market_niche` kind, no migration))
- [x] Nothing outside scope (no edits to `src/modules/market/**`, `trademark.ts`, `src/integrations/**`, `invai-contracts/**`; `evals/run.ts`'s retroactive grant was given but not used in this commit set — not a scope violation, just unused)
- [ ] Tests exercise the behavior, and none were weakened — mostly true (scan above), but the `simulate_price`/`get_price_position`-unavailable mock-disclosure path in finding 1 has no test at all, which is how it escaped
- [x] Tenancy (`withTenant`, explicit `companyId` filters in `designById`/`topDesigns`, cross-tenant `not_found` proven in `assistant-tools.test.ts` and live); no PII (orders counted, never listed); money in cents in `data`, formatted in `answer`; en/es text present and checked live in both languages
- [x] Idempotency: `recordRecommendationsShown` called once per turn in its own transaction (`service.ts`); not this card's write path otherwise
- [x] Decisions recorded where needed: credit-kind workaround, trademark threshold 60 (measured, tested), fallback-text choice, market eval standalone entry point — all documented in the report with rationale; the trademark-threshold decision is reasonable (measured against the full taxonomy, exact marks still caught) and not itself blocking

## Optional notes (not blocking)
- The answer-guard loop in `gateway.ts:266-278` only starts holding text once `guarded` flips true (on the first market `tool_call` event). Any text emitted *before* the first tool call in the same turn streams unchecked. In practice the model can't have seen tool data yet at that point, so this isn't exploitable for the injection scenario (AC14), but it's worth a comment or a test if a future prompt version lets the model narrate before calling a tool.
- The number validator (`src/ai/validators/answer.ts`) only recognizes digit-form numbers; a spelled-out number ("ninety percent") would bypass `unsupported_number` entirely. No eval case or test exercises this. Low practical risk (models render statistics as digits, and the prompt tells the model numbers are checked), but worth a defensive eval case given how central this validator is to the honesty guarantee.
- The author's report undercounts the QA acceptance-test reds (says "7 passed, 1 failed (AC33)" for `src/modules/ai/market.acceptance.test.ts`; my rerun on the same commit gets 2 failed, AC30 and AC33). Both trace to the same routed T-18-2 cause, so not blocking, but worth a corrected count in the next report.
