# Review of T-18-1 (round 1)

- Reviewer: web-engineer on Sonnet 5
- Author: architect on Fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-contracts && git log --oneline -3` | `378d6ae` follow-up (0.6.1, README + `market_niche` credit kind), `92b9260` market contract 0.6.0 |
| `cd invai-web && export PATH=... && pnpm typecheck` | `tsc --noEmit` — no errors (invai-web links `@invai/contracts` via `link:../invai-contracts`, so this typechecks against the landed contract) |
| `grep -n "market" invai-contracts/src/roles.ts` | `market.niches.manage` granted to owner/admin (via `SHOP_ALL`), OFFICE, DESIGNER; absent from PRESSER/PACKER/RECEIVER/vendor lists — matches spec AC24 |

## Consumer read as web-engineer (T-18-5)
Read `src/contract/market.ts`, `src/schemas/market.ts`, and the `AssistantEvent`/`AssistantMessage` additions in `src/schemas/ai.ts`. Everything T-18-5 needs to build the UI without guessing:
- `market.niches.taxonomy/get/set` and `market.recommendations.list/vote` are fully typed, additive, and the router key (`market`) matches the wave file's "Agreed interfaces".
- `RecommendationRef` (`id, rule, band, mock`) on `tool_result.recommendations` (max 3) and on `AssistantMessage.recommendations` is exactly the id-bearing shape the product-designer's spec review demanded (spec AC33) — I can bind a vote button to `id` from the live stream and, after a reload, from `AssistantMessage.recommendations` + `market.recommendations.list({ids})`.
- `tool_result.mock` / `sources: SignalSourceRef[]` give me the "Sample data" badge and source/date line without parsing answer text (AC3, AC30).
- `MarketRecommendation.vote`/`votedAt` plus the router's `errors: {}` (idempotent vote, no error surface needed) match AC33's "second tap shows stored state, not a second vote".
- `NicheTaxonomyEntry` (`key, family, labelEn, labelEs, peakMonths`) and `DesignNiches` (`niches: string[] ≤ 2, source, confidence, updatedAt`) are enough for the 0/1/2-niche chip states and a cmdk picker; `DesignNichesSetInput`'s own `.refine` (distinct niches) plus the router's `UNKNOWN_NICHE` error give me the failure case for free.
- Permissions match the UI split I need: `catalog.read` for niches read (designer has it), `market.niches.manage` for the niche picker (designer has it, presser doesn't), `finance.read` for recommendation list/vote (designer does **not** have it) — this alone lets me build AC24/AC6 (designer sees niche chip, never votes or price data) with `useCan()` and no extra plumbing.

## Nothing missing or awkward
No gaps found for what T-18-5 needs to build. Two small observations, neither blocking:
- `RecommendationParams` carries everything R1–R5's fixed copy needs (`channels`, `blankBelowReorderPoint`, `testPriceMinCents/MaxCents`, `floorPriceCents`, `ideas`, etc.) via `MarketRecommendation.params`, but that full object only comes back from `market.recommendations.list`, not from the stream's `RecommendationRef`. That's expected and fine — the wave file already says "the web renders vote cards from the event... reloads the rest with `list({ids})`" — just noting T-18-5 will do one `list({ids})` call per assistant turn that carries recommendations to get the action copy's params, rather than everything being inline on the event.
- `MarketAction`/`MarketRule` are enums; the fixed English/Spanish action templates (R1–R5) live in the spec's copy table, not the contract, which is correct per "the model does not invent actions" — confirms i18n keys are mine to add in `invai-web/src/i18n/{en,es}.ts`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Consumer can build UI without guessing | yes | See "Consumer read" above; every field T-18-5's card cites (chips, badge, votes, niche chip) is present and typed |
| `pnpm typecheck` passes in invai-web | yes | `tsc --noEmit` clean |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed by T-18-1 (`invai-contracts/src/contract/market.ts`, `src/schemas/market.ts`, `src/contract.ts`, `src/schemas/ai.ts`, `src/roles.ts`+test, `src/index.ts`, `package.json`, `CHANGELOG.md`, README per its follow-up grant) — not re-verified line-by-line here (that's the primary `reviewer`'s job); I confirm only that nothing under `invai-web/**` was touched.
- [x] Nothing outside scope, from a consumer's view
- [ ] Tests / weakened-test scan — out of scope for a consumer co-review; deferred to the primary `reviewer`.
- [x] Additive: new enum values (`get_market_trend`, ...) at the end of `tool_call.name`; new optional fields on `tool_result`/`AssistantMessage`, no new discriminated-union member — safe for a web build that may run a version behind.
- [ ] Decisions recorded where needed — ADR 0015 (global cache) is architect's; not reviewed here.

## Optional notes (not blocking)
- Recommend the product-designer's suggested shared `ConfidenceBadge` land in `invai-ui` before wave 19's digest, so market-signals and the digest don't grow two ad hoc band treatments; T-18-5 will build a local one in `invai-web/src/components/market/` in the meantime and report it, per its card.
