# Review: T-P3-1 Rate-limit buckets by intent (security co-review, round 1)
Reviewer: security-reviewer on opus. Author: backend-foundation on fable/sonnet. Commit: invai-backend `b5c649f`.

## Verdict: approve

## Threat model (who, what session, whose data, worst outcome)
- Change: 3 non-GET procedures move `writes` (120/min) → `reads` (300/min), per company. Worst plausible outcome: 2.5x more of a looser call per tenant. Only matters if a moved call writes, enqueues, signs an upload, renders or costs money, or leaks across tenants. None does (below).

## Evidence I re-ran / read
| Check | Result |
|---|---|
| `pnpm exec vitest run src/api --reporter=dot` | 12 files, 67 tests passed (exit 0; vitest close-timeout noise only) |
| `git diff b5c649f~1 b5c649f -- src/lib/ratelimit.ts` | empty: capacities/refill unchanged |
| `bucketFor` diff (`src/api/orpc.ts:186-195`) | `ai.*` and `auth: "station"` branches byte-identical and still first; only the final non-GET line changed |

## Per-procedure check of `NON_GET_READS`
- `files.downloadUrl` (`modules/files/service.ts:106-131`): `isSafeKey`, then key must start with `${companyId}/` or pass `vendorCanRead`; else `NOT_FOUND`. `canReadKind` applies per key kind. `headObject` runs only after the tenant check, so there is no cross-tenant existence oracle. Presigns a GET only, no PUT, no write. A higher rate gives no enumeration advantage: foreign keys always return the same `NOT_FOUND`.
- `skuRules.test` (`modules/channels/sku.ts:536+`): regex is bounded (`MAX_PATTERN_LEN` 200, `unsafeRegexReason`, `execSku` caps sample length `MAX_SKU_MATCH_LEN`); catalog read under `withTenant`; no write.
- `skuRules.suggest` (`sku.ts:733+`): reads only, under `withTenant`; `channelSkus` is capped at 200 in the contract. The contract's `useAi` flag is **ignored** by the backend (heuristic only, `sku.ts:~885` comment), so no paid model call moves to `reads`.
- Everything that writes, renders, calls out or writes storage stays `writes`: preview, supplier stock, batchLabelPdf, exports, demo.*, alerts, notes, digest, votes. The author kept `inventory.suppliers.stock` and `shipping.batchLabelPdf` in `writes`, which is stricter than the architect's candidate list. I agree: both write storage or call out.

## Can a caller influence the bucket?
No. `path` is the server-resolved procedure path. `method` is read from the procedure's static contract route (`procedure["~orpc"].route.method`), not the HTTP request, so RPC and REST transports and any spoofed method or input pick the same bucket. The membership test is an exact string match on the joined path.

## Test pins the classification
`buckets.test.ts` walks `listProcedures(contract)`. Any new non-GET `.read` procedure fails until someone classifies it, and every `NON_GET_READS` entry must be a non-GET `.read` procedure (so a write permission can't be slipped into `reads`). Good. It meets AC3.

## Blocking findings
none

## Optional notes
- Follow-up for ai-engineer and architect: if `skuRules.suggest` ever honours `useAi`, it must leave `NON_GET_READS` or route the AI part through the `ai` bucket. Consider a comment next to the set entry. The gateway's spend breaker would still cap the cost.
- Not security, for the tech lead: the author's report says they killed PID 31268 (another session's API on :3142) by mistake.
