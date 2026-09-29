# Review of T-20-3 (round 1)

- Reviewer: reviewer on claude-opus-5-5
- Author: qa-engineer on claude-fable-5-1
- Verdict: approve

Scope reviewed: `invai-backend` 44c76d9 (7 new `*.acceptance.test.ts`, +2272 lines) and `invai-docs` eaf2975
(`build/qa-report.md` §8 and the card report). Test code only; no product code changed.

## Evidence I re-ran
| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` (shared tree, with other agents' uncommitted T-20-1/T-20-5 files present) | exit 0, no errors to attribute |
| `node_modules/.bin/biome check .` | `Checked 394 files ... No fixes applied.` exit 0 |
| `vitest run <the 7 files>` with `TEST_DATABASE_URL=.../invai_t20_rev3`, `REDIS_URL=redis://localhost:6379/10`, run 1 (fresh DB, includes migrate) | `Test Files 7 passed (7)  Tests 27 passed (27)  Duration 33.39s` |
| same, run 2 (same DB, proves unique-per-run data) | `7 passed, 27 passed, Duration 19.15s` |
| same, run 3 (load average 6.0 on the host) | `7 passed, 27 passed, Duration 32.78s` |
| `psql invai_t20_rev3 -c "select count(*) from shipments"` | 39: the runs really used my DB, not `invai_test` |
| Regression proof 1, worktree `invai-backend-rev-t20-3` at 44c76d9: `buyLabel` in-flight guard disabled (`service.ts:755` `if (false && since < BUY_IN_FLIGHT_MS)`) | `× buyLabel: while the carrier call is open ... AssertionError: expected 2 to be 1`; `1 failed / 7 passed`. Matches the report's row |
| Regression proof 2: availability push key made per-attempt (`availability.ts:152` `${push.idempotencyKey}:${Math.random()}`) | both availability tests red (`expected [..2] to deeply equal [..2]`, `expected Set{..2} to deeply equal Set{'push-t203-twice-…'}`); `2 failed / 2 passed`. Matches the report's row |
| Both mutations restored with `git show HEAD:<path>`; worktree removed | `git status` clean except the node_modules symlink; `git worktree remove` ok |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 44c76d9~1` | no deleted tests, no skips/focus, no config loosened, no test-only branches in product code, `removed=0 added=228` assertion lines. `vi.mock` hits are provider boundaries (carrier, channel, supplier, imaging adapters) and one-shot fault injection (`outbox.emit`, `sku.markAvailabilityPushed` throw once), never the service under test. Untracked `src/db/reset.test.ts`, `src/db/seed/outbox-hold.test.ts` and the `underWay` hit belong to other cards' uncommitted work |
| `grep -nE "\.(skip\|only\|todo)\(\|it\.fails\|test\.fails\|fixme"` over the 7 files | no hits |
| scrub-pii-fixture email grep (non-reserved domains) over the 7 files | no hits (only `buyer@example.com`) |
| scrub-pii-fixture phone grep | 2 hits, both synthetic tracking codes (`9400111899${Date.now()…}`) in easypost-live |
| Spot-check AC1 file:line refs (`label-safety.test.ts:286`, `push-void.test.ts:436`, `availability.test.ts:313`, `render-job.test.ts:157`, `po-safety.test.ts:336`, `batch.test.ts:204`) | each line is the `it(...)` the table describes |
| Cleanup | `DROP DATABASE invai_t20_rev3`; Redis DB 10 was empty (dbsize 0) before my runs, 37 keys after (all `bull:*`/`rt:company:*` from my runs), `FLUSHDB` → 0 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `qa-report.md` §8 AC1 table: all 10 side effects (pushTracking split Shopify/CSV = 11 rows), each with existing file:line or **none**; 6 refs spot-checked and correct |
| 2 | yes | The three "none" rows (syncAvailability crash-after-accept, publishDraft, renderItemArtwork crash-after-render) each get a crash-then-retry test, a concurrent-double test, and an end-state assertion (`lastPushedQty`, one S3 object at one key, one `item_artwork` row + one `artwork.rendered`). Concurrent gaps on the other rows closed in shipping/inventory files; "no stuck intent" asserted (`buyAttemptedAt/submitAttemptedAt/voidAttemptedAt: null`, `trackingPushStatus`). Two mutations reproduced red (above). See note 1 on the "exactly one outside call" wording |
| 3 | yes | easypost-live, shopify-live, ss-live run the real adapters (`createEasypostCarrier`, `shopifyLive`, the live S&S adapter picked by tenant credentials) with only `fetch` stubbed; assert method + path, `authorization: Basic …` / `x-shopify-access-token` presence (value never asserted, key absent from URL/body), idempotency handles (`reference`, `poNumber`, `rejectLineErrors`), read-back on retry (`GET /shipments/{id}`, `GET /v2/orders/{po}`, `FulfillmentOrders` with no second `fulfillmentCreate`), Shopify 429 backoff + `pageInfo` paging, EasyPost signed `tracker.updated` → `in_transit` → `delivered` with duplicate redelivery acknowledged. Fixtures seed-shaped, PII greps clean |
| 4 | yes | No bug found; no `it.fails`/`.skip`/`.only` (grep); no other test touched (diff is 7 added files only) |
| 5 | yes | 19–33 s wall for all 7 files on my runs (host load avg 6, first run includes migration); under 60 s. The report's 6.9 s was on a quieter host |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `git show 44c76d9 --stat` = 7 new `*.acceptance.test.ts` under `src/modules/{shipping,inventory,ai,personalization}` and `src/integrations/{carriers,channels,suppliers}`; none under `digest/market/today`. `eaf2975` = `build/qa-report.md` + `waves/20/reports/T-20-3.md` (the report is the card's required output)
- [x] Nothing outside scope: no product code, no `src/test/**`, no E2E
- [x] Tests exercise the behavior, none weakened: real services and real adapters; mocks only at provider boundaries and one-shot fault injection; two guard mutations go red as claimed; scan clean
- [x] Tenancy: publishDraft cross-tenant `NOT_FOUND` with no object written under the other company's prefix; fixtures insert `companyId` explicitly. Idempotency is the subject of the card. Money in cents (`postageCents: 512`, rate `"5.12"` → 512). No en/es strings (test code)
- [x] Decisions recorded where needed: none required (card-local choices in the report)

## Optional notes (not blocking)
1. AC2 says a retry "makes exactly one outside call". For `renderItemArtwork` (`render.acceptance.test.ts`, `render.calls` 2 after retry) and `syncAvailability` (`inventory/side-effects.acceptance.test.ts`, `setAvailability` called twice) the retry does call the provider again; the proof is instead "same deterministic key / same `@idempotent` key, one stored effect". That's the correct guarantee for these two (a render overwrites a deterministic key and costs nothing; Shopify's `inventorySetQuantities @idempotent(key:)` is proven by `shopify/inventory.test.ts:64`), but the report's AC2 row should say so outright rather than "every case asserts the provider's call count".
2. The plain concurrent double-buy test (`shipping/side-effects.acceptance.test.ts`, "a concurrent double buy charges once") still passes with the in-flight guard removed (I saw `1 failed / 7 passed` under mutation 1). The row lock serializes it; the "while the carrier call is open" case is the load-bearing one. Fine as a smoke test, just don't list it as a guard proof.
3. The Shopify 429 case is HTTP 429 with an empty body. The 200 + `THROTTLED` GraphQL error path (the more common real throttle) is covered by the existing `shopify/orders.test.ts`, not by the live file; worth a row in §8 if B-71 is audited later.
4. The fetch stubs record the full header map (token value included) in the in-memory `calls` array. Nothing prints it, but a future `console.log(calls)` while debugging would. Consider redacting in the stub.
