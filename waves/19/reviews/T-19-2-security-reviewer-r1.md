# Review of T-19-2 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: ai-engineer on Opus 5.5
- Verdict: approve

## Scope of this review
Co-review lens only: prompt injection through shop-typed names in `digest_narrative` facts, PII
scrub before the model call, shadow-mode text can't reach a client, the breaker's blast radius,
and tenant isolation in the extracted analyst queries. Correctness/AC coverage otherwise already
verified by `reviewer` (r1, approve); I re-derived the security-relevant parts independently
rather than trusting that file.

## Evidence I re-ran
Worktree `/tmp/invai-backend-sec-t19-2` at `ed68608` (symlinked `node_modules`, own `.env` with
`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` at `invai_t19_sec`, `REDIS_URL` db 9).

| Command | Result |
|---|---|
| `vitest run src/ai/digest-narrative.test.ts src/ai/validators/digest.test.ts src/modules/ai/analyst-queries.test.ts` | `3 files, 35 passed` |
| Read `src/ai/pii.ts`, `src/ai/gateway.ts:180-241` | `runStructured` runs `stripPiiDeep(sanitizeDeep(vars))` before every model call, including `generateDigestNarrative`'s call — PII scrub is structural, not opt-in per route |
| Read `src/modules/ai/analyst-queries.ts` (`fulfillmentHealth`, `designInsights`, `comparePeriods`, `adPerformance`) in full | No buyer field (`buyerName`, `shipTo`, `buyer_note`, email/phone/address columns) is selected anywhere; every row is a count, sum or design/channel/reason label. Matches the file's own comment ("No buyer PII: orders are counted, never listed") |
| Read `src/ai/prompts/index.ts` `dataBlock()` / `DATA_RULE` | Facts (including shop-typed design names) reach the model as JSON inside a `<data source="digest_facts">` block, `<` escaped to `<` so no input can close the block or forge a new `<data>` tag |
| Read `src/ai/validators/digest.ts` `validateNarrative` | Every rule (`digits`, `number_words`, `direction_words`, `promise`, `url`, `email`, `markup`, `market_claim`, `pii`) runs on `ownWords()` — the model's text with every well-formed `{{factId}}` placeholder removed first. A hostile fact value can therefore only ever appear as a substituted value, never as text the rules judge as the model's own claim |
| `grep -rn "generateDigestNarrative\|showable" src/` (whole tree, not just this diff) | Only `src/ai/digest-narrative.ts` and its test call `generateDigestNarrative`; no email, delivery or web/floor code reads it yet (T-19-3's digest module is still a stub router — `cadc338`). There is no live path today for shadow text to reach a client; that gate becomes T-19-3's to prove when it wires the digest module to this function |
| Mutation test 1: commented out `if (stripPii(p.text) !== p.text) failed.add("pii")` in `validators/digest.ts`, ran `vitest run src/ai/validators/digest.test.ts -t pii` | Failed as expected: `expected [ 'url', 'email' ] to include 'pii'` — the `pii` rule is load-bearing beyond what the url/email regexes already catch. Restored; full file `15/15` clean after |
| Mutation test 2: commented out the `placeholder_foreign` branch (an item using another insight's fact id) | Failed as expected: `expected [] to deeply equal [ 'placeholder_foreign' ]`. Restored; full file `15/15` clean after |
| Mutation test 3 (tenancy): in `fulfillmentHealth`, replaced `eq(orderItems.companyId, ctx.companyId)` with `sql\`true\`` (dropping the explicit tenant filter that feeds `itemsPlaced`), ran `vitest run src/modules/ai/analyst-queries.test.ts -t "count only"` | Failed exactly as a cross-tenant leak would: `expected 3 to be +0` for `mixed.totals.itemsPlaced` (company B's context inside company A's `withTenant` transaction). Proves the explicit `company_id` filter is doing real work on top of RLS, not decoration — if RLS session and `ctx.companyId` ever disagree (e.g. a future caller bug), the filter is the second line of defense that the test actually exercises. Restored; `3/3` clean after |
| Cleanup | Test DB `invai_t19_sec` dropped, Redis DB 9 flushed, worktree removed (`git worktree list` shows only `main`) |

## Acceptance criteria (security-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 3 Validator / AC19 | yes | Hard-fail rules run on placeholder-stripped model text; mutation-tested `pii` and `placeholder_foreign` myself (above) |
| 4 Injection / AC20 | yes | Structural: `dataBlock` JSON-encodes and escapes `<`; validator strips placeholders before scanning for banned content, so the injected design name text can only surface as a substituted value. Eval cases dn-006/007/008/020 (en, es, `</data>` breakout, `<script>`) exist and pass in mock mode (confirmed in the author's report and by reading `evals/digest_narrative/cases.jsonl`) |
| PII scrub before the call | yes | `runStructured` scrubs `vars` (`stripPiiDeep(sanitizeDeep(...))`) before any provider call; independently, the facts sent for digests never contain buyer fields (verified by reading every analyst-query function, not just trusting the file's comment) |
| Shadow can't leak to a client | yes, for this card | `showable` is `true` only for `mode === "on" && status === "ok"`; no consumer exists yet in the tree, so there is no leak path today. This gate must be re-checked when T-19-3 wires the digest module to `generateDigestNarrative` — flagging for that card's review, not blocking here |
| Breaker cross-tenant blast radius | acceptable, with a note | `checkDigestSummaryBreaker` reads counts only via `withSystem` (no row content leaves the function) and on trip only *narrows* behavior (flips global mode to `shadow`, which is already today's default and the fail-safe state) — it cannot expose data or grant access across tenants. One tenant generating enough rejected summaries could globally disable the AI summary for every other tenant (denial-of-feature, not denial-of-service on the product, since digests still ship with template text). This is exactly what spec AC22 asks for (a global breaker) and is currently low-impact because `on` isn't set anywhere in this wave. Recorded as a known, accepted shape of the control, not a finding — worth a one-line note in the OI-8 real-model rollout review about a per-company sub-threshold or alert-only first step before any wave turns `on` on by default |
| Tenant isolation of extracted queries | yes | `analyst-queries.test.ts`'s "count only the caller's tenant" test asserts the exact cross-tenant scenario (mismatched `ctx.companyId` inside another tenant's `withTenant` transaction); mutation-tested it myself (above) to confirm it is a real, load-bearing check rather than a tautology |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git -C invai-backend diff --stat 759f2d4^ 759f2d4` / `ed68608^ ed68608`, re-read against the card's owned globs; matches `reviewer`'s r1 findings, independently spot-checked `src/db/schema/ai.ts`'s 3-line diff — enum values only, no migration)
- [x] Nothing outside scope for a security lens (no digest delivery, email or web/floor code touched; `assistant-tools.test.ts` untouched)
- [x] Tests exercise the behavior, and none were weakened — confirmed by mutation-testing three security-relevant rules/filters myself (pii, placeholder_foreign, tenant filter) rather than only reading the assertions
- [x] Tenancy: every analyst-query function filters explicitly on `ctx.companyId` in addition to relying on RLS (`withTenant` opened by the caller); the one `withSystem` use (`digestSummaryRejectRate`) is counts-only, consistent with the documented `withSystem` exception list (breaker, no row content)
- [x] No buyer PII reaches the model: verified by reading every analyst-query function (not selected) and by the gateway's structural `stripPiiDeep` scrub on every call
- [x] Decisions recorded where needed — none of my findings needed a new `decisions/` entry

## Optional notes (not blocking)
- When T-19-3 wires the digest module to `generateDigestNarrative`, its review should grep for every place the returned `text`/`summary` is stored or rendered and confirm `showable` (not `status === "ok"` alone) gates anything shown to a shop or put in an email. Today nothing reads it, so there is nothing to check yet, but this is the seam where a shadow leak would first become possible.
- Before any future wave sets `DIGEST_SUMMARY_MODE=on`, consider whether the global breaker should also be visible per-company (e.g. in the alert `data`) so a chronically-rejecting shop's summaries can be diagnosed without guessing which shop tipped a global flag — a usability note for the breaker's operator, not a security gap.
