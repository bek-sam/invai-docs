# Review of T-P5-4 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran (own worktree /tmp/p5-rev-t4 at cdeb3e3, scratch DB invai_p5rev_t4, Redis db 13; worktree and DB removed after)
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check src/modules` | exit 0 / 226 files, no fixes |
| `vitest run src/modules/today src/modules/orders/timeline.test.ts` | 4 files, 67 passed |
| Same 2 new/changed test files with the 6 product files set back to 0aa67d8 | 46 failed, 4 passed (red on the old code; the 4 are the fallback guards) |
| Mutation: drop `incoming`, `sheetStatus`, `usedPct` from generateAlerts params | today: 37/37 still pass (survives) |
| Mutation: toAlert skips `AlertParams.safeParse` and returns raw params | 20/20 still pass (survives) |
| Mutation: vendors params without `vendorName`, webhook params `{}` | today+vendors+channels jobs: 60/60 pass (survives) |
| `scan-test-weakening.sh invai-backend 0aa67d8` | 2 hits (`expect.any(String)` for orderNo/shipBy, backed by the exact message assert). Nothing removed |
| Read-only dev DB: open alerts by `data->>'messageCode'`; distinct `order_item_transitions.reason` | sheet_stuck/stock_low/order_* rows carry keys exactly as R1, ISO shipBy. All 12 live reasons map to a code |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes (code) | All 14 codes: keys match R1 / `ALERT_MESSAGE_PARAM_KEYS`, nested in `data`. ISO dates. title/message unchanged. Only alert reader is `listAlerts`→`toAlert`. Code is right, but see finding 1 for its tests |
| 2 | yes | `reasonCodeFor` follows R1 order (state first, exact strings, 3 patterns, reprint param only if in REPRINT_REASONS, unknown → {}). Table test of 31 cases plus a timeline() integration test, red on base |
| 3 | **no** | Per-kind tests cover only order_overdue, order_at_risk, sync_broken (service.test.ts:131-155). Finding 1 |
| 4 | yes | re-raise test: same id, 1 row, params updated. Upsert `set.data` carries the nested code |

## Blocking findings
1. `src/modules/today/service.ts:399,419,443` (sheet_stuck, stock_low, plan_limit_near/reached): AC3 asks for one test per alert kind changed. These four codes are in owned files and are raised by `generateAlerts`, which is easy to test, yet no test checks their params. The `it.each` round trip feeds hand-made sample params into `raiseAlert`, so it never runs these call sites. Failure scenario: someone drops `incoming` or `sheetStatus`, or renames `usedPct`, and every test stays green (proved by mutation). The Spanish Today line then shows a blank or "undefined". Fix: assert messageCode plus exact keys for each of the four in the generateAlerts test (set a low stock row, a sheet sent >24h ago, and an orders meter ≥0.9 and at the limit).
2. `src/modules/today/service.ts:208` (also AC3 / R1): R1 says `toAlert` drops both fields when the params fail `AlertParams.safeParse`. No test covers it: only the unknown-code and no-code cases are tested, and the mutation that removes the check survives. Failure scenario: a later edit drops the check. A row with a known code but bad params (say a 200-char sheetName, or `channel: "easypost"`) then goes to the web, or fails output validation for the whole alerts list. Fix: insert a row with a known code and invalid params, and assert both fields are absent.

## Checks
- [x] Only owned paths changed (8 files; call-site edits are the alert input objects only; shared tree's dirty `src/db/seed/builder.ts` is another card's, excluded)
- [x] Nothing outside scope (no producer, migration or worker/AI change)
- [ ] Tests exercise the behavior: timeline yes; alerts partly (findings 1-2). None weakened
- [x] Tenancy unchanged (no new withSystem in product code), idempotency kept (dedupe upsert), no PII in params, no money, no UI text
- [x] Decisions: none needed

## Optional notes (not blocking)
- The 7 cross-module call sites (shipping/inventory/channels/vendors) have no behavior test either. Their test files are outside the owned paths. Tech lead: grant those test paths or accept the gap.
- `po_stuck_submitting.supplierName` is the raw code (`s_and_s`), and the vendor fallback is the English "the vendor". Both reach the Spanish line. Follow-up for T-P5-5 or the backlog.
- I didn't start an API: dev DB rows and the listAlerts/timeline integration tests cover the output path.
