# Review of T-29-4 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer on Opus 5.5 (card says sonnet; no high-risk flag, so same-model is allowed)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm vitest run src/modules/channels --reporter=dot` (HEAD 384ef6f, tree clean) | 9 files, 58 passed |
| `pnpm exec biome check src/modules/channels` / `pnpm typecheck` | 14 files clean / tsc exit 0 |
| New test file on base 95324fe (scratch worktree, removed) | 3 failed, 3 passed (skip, dedupe+re-enable, per-connection red; 3 regression guards green) |
| Mutant `if (!known)` -> `if (true)` (skip every order event while off) vs the card's tests | **6/6 still pass** |
| Probe (2 tests, same worktree, deleted): Etsy `ORDER_CANCELED` (order_ref) for a known order with auto-import off; Shopify `orders/updated` with newer `updated_at` | real 47ce0ee: 2 pass (status `cancelled`; `channelUpdatedAt` 10-01 -> 10-05). Mutant: 2 fail (`needs_attention`; stays 10-01) |
| `scan-test-weakening.sh invai-backend 95324fe` | channels file: additions only; the 3 removed assertions belong to T-29-2 (`src/lib/account-security.test.ts`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | test 1 (no order, `handled: true`, `lastWebhookAt` set); log has companyId/connectionId/channel/topic only |
| 2 | behavior yes, proof no | code is right (my probe), but tests 3-4 don't catch the always-skip mutant: finding 1 |
| 3 | yes | cursor untouched (`markConnection` webhook sets only `lastWebhookAt`, service.ts:604-605); manual sync imports once, poll still skips. Etsy has no `fetchOrders` (pending approval) and live `fetchOrder` throws, so no Etsy regression; author lists it |
| 4 | yes | test 5 (true and unset); red-on-base split confirms |
| 5 | yes | test 2; skipped delivery stays `processed` and re-send is deduped, which decision 0030 ("acknowledged and skipped", recovery by Sync now) accepts |

## Blocking findings
1. `src/modules/channels/webhook-auto-import.test.ts:141-149` (and no Etsy case) — the "known order still applies" half of AC2, the decision's main safety rule ("a missed cancel can cause a wrong print"), has no test that fails if it breaks. Test 3 uses a Shopify refund, which parses as `order_cancelled` and never enters the new branch; test 4 asserts only one row, which an always-skip also yields. Scenario: a later edit drops the `known` check (or keys it by the wrong column); Etsy cancels arrive as `order_ref` and are skipped, a cancelled order is printed, and the suite stays green. Fix: in test 4 assert a field the update changes (e.g. `channelUpdatedAt` with a newer `updated_at`), and add an Etsy `ORDER_CANCELED` for a known order with auto-import off that asserts `status === "cancelled"` (mock `mockEtsyReceipt` cancels ids divisible by 10). Both must fail under the mutant above.

## Checks
- [x] Only owned paths changed (`sync.ts`, new test file in `modules/channels`)
- [x] Nothing outside scope (route, verification, dedupe untouched)
- [ ] Tests exercise the behavior: finding 1; none weakened
- [x] Tenancy: existence check in that connection's `withTenant`, key (company, channel, channelOrderId) matches the unique index; per-connection `continue` before `fetchOrder` (at most one live row per shop anyway, `channel_connections_connected_shop_uq`)
- [x] Decisions recorded (0030)

## Optional notes (not blocking)
- Test 6 uses two shops, so it can't tell `continue` from `return`; harmless given the unique index.
- `conn.settings as {...}` cast mirrors `syncConnection`; fine.
