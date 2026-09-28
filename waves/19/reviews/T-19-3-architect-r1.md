# Review of T-19-3 (round 1)

- Reviewer: architect on Sonnet 5
- Author: backend-engineer (digest) on Opus
- Verdict: approve

Scope of this co-review (card + `wave.md`): cross-module interfaces only — finance/ai/market/notify
boundaries, contract conformance of router output, `digest.ready` payload, delivery-idempotency
layering (A7), preview limit (A8), click-handler shape (A9). I did not re-judge tenancy/RLS
(security-reviewer's scope) or migration mechanics (backend-foundation's scope), and I left
`render.ts:282` (empty `{{channels}}` sentence) alone as instructed — it is a round-2 fix in
progress by another agent.

## Evidence I re-ran

Read-only in the shared tree at `bef6158` (no worktree needed; no writes, no `pnpm`, no DB commands run).

| Check | Result |
|---|---|
| `git show cadc338 bef6158 --stat` | Only `invai-backend/src/modules/digest/**`, `src/db/schema/digest.ts` + `drizzle/0029_digest.sql`/meta, and the three granted one-line registrations (`src/db/schema/index.ts`, `src/api/router.ts`, `src/modules/jobs.ts`). Matches owned paths. |
| Read `src/modules/digest/snapshot.ts` | Uses `comparePeriods`/`adPerformance`/`designInsights`/`fulfillmentHealth` (T-19-2's `analyst-queries.ts`) and `getProfit` (finance) as functions, and `lowStockItems` (inventory) as a function — no direct table access to any of those modules' owned tables |
| Read `src/modules/digest/service.ts` | Uses `getStatus` (billing), `creditBalance`/`digestSummaryMode` (ai), `listRecommendations` (market), `getEmailPreferenceTx`/`isSuppressedTx`/`listEmailPreferencesTx`/`setEmailPreferenceTx` (T-19-4's `lib/notify.ts`), `isPlaceholderEmail` (integrations/vendors/mailer) — all as exported functions, none reaching into those modules' tables |
| Read `src/modules/digest/deliver.ts` | Uses `sendUserEmail`/`buildMessageId`/`emailFooter`/`unsubscribeLink` (notify), `signLink` (links), `listRecommendations` (market) — same pattern |
| `grep -n "from \"\.\./orders\|from \"\.\./channels\|from \"\.\./finance\|from \"\.\./production\"" src/modules/*/service.ts` | Confirms other rollup-style modules (`today`, `market`, `ai/analyst-queries`) reach across module boundaries the same way |
| Read `src/modules/today/service.ts` (precedent) | `summary()` reads raw `orders`, `order_items`, `gang_sheets`, `scans`, `shipments`, `members` directly via `sql` with a doc comment ("Counts across modules are read-only aggregates (tolerated reads of foreign tables)") — the established pattern for a cross-module rollup module |
| `grep -n "^export" src/modules/channels/service.ts` | `listConnections` returns current-state `ChannelConnection[]` only; no exported function answers "disconnected or errored **during a given week window**" — D1's own query has no service equivalent to call instead |
| Read `src/modules/digest/snapshot.ts` `unhealthy()`, the `overdueRows`/`incompleteOrders` block, `lowStockForTopDesigns()` | Direct, read-only `SELECT`s on `orders`, `channel_connections`, `profit_lines`; each has a doc comment naming why (a controllable `asOf` instant tests can freeze, no existing service answers the exact shape); no writes, no PII columns selected (channel/status/blank/design ids and counts only) |
| Read `src/modules/digest/service.ts` `recipients()` | Direct read of `members`/`users` filtered on `finance.read`-holding roles (`FINANCE_ROLES`, derived from `ROLE_PERMISSIONS`, the same static table the permission guard uses) — a recipients-by-permission query with no existing service export either |
| Read `invai-contracts/src/contract/digest.ts` + `src/schemas/digest.ts` | Router procedures, permissions (`finance.read` reads, `org.manage` settings/preview), routes and I/O schemas match `bef6158`'s `router.ts` exactly |
| Read `src/modules/digest/service.ts` `toSummary()` | `status: row.status === "skipped_quiet" ? "skipped_quiet" : "ready"`; only ever called on rows already filtered to `["ready","skipped_quiet"]` (`VISIBLE`) in `listDigests`/`visibleByWeek`/`latestDigest` — `building`/`failed` never construct a `DigestSummary` |
| `grep -n "\.narrative\b" src/modules/digest/service.ts` | No hit outside `contentOf`'s explicit field list; `getDigest`'s output object is built field-by-field, no `...row` spread — confirms no narrative text leaks through `digest.get`/`list`/`latest` (contract has no text field in 0.7.0 at all) |
| Read `service.ts` `getDigest()` planUsage gate | `if (ctx.permissions.has("billing.read")) out.planUsage = await planUsage(...)` — matches contract's `planUsage: DigestPlanUsage.optional()` and A2 |
| `grep -n "digest\.ready" src/modules/digest/build.ts ../invai-contracts/src/events.ts ../invai-contracts/src/realtime.ts` | `build.ts` emits/publishes `{ digestId: row.id, weekKey }`; both `events.ts` and `realtime.ts` declare `"digest.ready": z.object({ digestId: Id, weekKey: WeekKey })` — exact match, envelope carries the org as agreed |
| Read `src/modules/digest/deliver.ts` `deliverDigest()` | Per-recipient `digest_deliveries` row inserted `pending`/`skipped` before any send, updated after; the send call itself goes through `sendUserEmail` (T-19-4's `email_sends`, dedupe key `digest:${digestId}:${userId}`); a `duplicate` skip from `sendUserEmail` is folded back to `sent` locally — matches A7's two-layer design (email_sends owns send idempotency, digest_deliveries is the outcome row) |
| Read `sendPreview()` | Redis `SET NX EX` on `digest:preview:${companyId}:${userId}`, `C.preview.windowSec`; ids from the session (`router.ts` `person(context.tenant)`), never from client input; `RATE_LIMITED` mapped to a `Retry-After` header in `router.ts` — matches A8 exactly (only the opt-in check is bypassed; the "ready digest exists" check still applies, giving `NO_DIGEST` when there is none) |
| Read `src/modules/digest/jobs.ts` `registerLinkHandler("click", ...)` | Signature `({companyId, userId, ref}) => Promise<{path} | null>`; validates `ref` splits into two UUIDs before calling `clickTarget`, returns `null` on anything invalid — matches A9's shape; `clickTarget`'s `href` values are all hardcoded internal paths per `market-watch.ts`/`detectors.ts` (`hrefOf`, `COST_LINE_HREF`), so same-origin holds structurally |
| Cross-check against reviewer/security-reviewer/backend-foundation r1 files | All three already approve; nothing in their evidence conflicts with what I found on the boundary/contract questions in my scope |

## Acceptance criteria (my scope only)

| # | Item | Met? | Evidence |
|---|---|---|---|
| 1 | finance/ai/market/notify used only through public services | yes | `snapshot.ts`, `service.ts`, `deliver.ts` call named exports (`getProfit`, `comparePeriods`/`adPerformance`/`designInsights`/`fulfillmentHealth`, `generateDigestNarrative`/`digestSummaryMode`, `listDigestMarketItems`/`recordRecommendationsShown`/`listRecommendations`, `sendUserEmail`/`signLink`/`registerLinkHandler`) — no import of another module's schema table outside the four listed exceptions |
| 2 | The 4 listed direct table reads (orders, channel_connections, profit_lines, members) are acceptable | yes, judged below | see "Direct reads" |
| 3 | Router output matches 0.7.0 contract schemas | yes | permissions, routes, input/output types in `router.ts` match `contract/digest.ts` line for line; `toSummary`/`getDigest` build `Digest`/`DigestSummary` shapes that satisfy the zod schemas (statuses restricted to the two client-visible values, no text field, `planUsage` optional and gated) |
| 4 | `digest.ready` payload matches contract | yes | `{digestId, weekKey}` in `build.ts`, `events.ts`, `realtime.ts` all agree |
| 5 | Delivery idempotency layering matches A7 | yes | `email_sends` (T-19-4) owns send-dedupe; `digest_deliveries` is the per-recipient outcome row, settled after the call, never re-touched once `sent`/non-`pending` |
| 6 | Preview limit matches A8 | yes | per-user Redis key, 60 s TTL, `RATE_LIMITED` with `Retry-After`; bypasses only the opt-in check |
| 7 | Click handler matches A9 | yes | `registerLinkHandler("click", ...)` signature, ref format, same-origin hrefs |

### Direct reads, judged individually

- **`orders`** (overdue-by-channel count, incomplete-profit-lines count): no existing orders-module
  export answers "count grouped by channel, overdue as of an instant the caller controls" or "orders
  with items but no profit line yet" — and both need a controllable `asOf`/window that a service
  built around `now()` wouldn't give tests. `today/service.ts` reads the same table directly for the
  same reason (a rollup module's own time window). **Acceptable**, same pattern as `today`.
- **`channel_connections`** (D1: error now, disconnected during the week, or errored during the
  week): `channels/service.ts`'s only export, `listConnections`, returns current state only, not a
  week-windowed history. No service to reuse. **Acceptable**.
- **`profit_lines`** (D7: which blanks the week's top designs used): a link query (design id →
  blank id) with no natural home in `finance/service.ts`'s public surface, which is about totals and
  cost lines, not per-line blank/design pairs. Read-only, no money fields recomputed from it (money
  still comes from `getProfit`). **Acceptable**.
- **`members`/`users`** (recipients: active members whose role holds `finance.read`, plus email
  state): this is exactly the kind of permission-derived query `today`, `billing` and others don't
  currently expose as a shared function either; it's computed from the same static `ROLE_PERMISSIONS`
  table the guard itself uses, not a role-name guess, so it can't drift from the real permission set.
  **Acceptable**.

None of the four writes to another module's table, none touches buyer PII, and each has a doc
comment explaining the exception — matching the standard this codebase already sets with `today`'s
"tolerated reads of foreign tables." I'd rather these stay documented tolerated reads than force a
one-off service export in finance/channels/orders that only this card would call; if a second
consumer ever needs the same query, that's the trigger to promote it to a real service function.

## Blocking findings

None.

## Checks

- [x] Only owned paths changed (`git show cadc338/bef6158 --stat`; matches the card's globs and the
  three named grant lines exactly)
- [x] Nothing outside scope for my co-review area (cross-module boundaries, contract conformance)
- [x] Tests exercise the behavior — not re-verified independently in my scope; reviewer/security/backend-foundation's r1 files already cover this with re-run commands, and nothing I read contradicts their findings
- [x] Tenancy / idempotency / money in cents / en-es — out of my primary scope this round (owned by
  security-reviewer/backend-foundation), but nothing I read while tracing the cross-module calls
  contradicts their approvals
- [x] Decisions recorded where needed — none needed; the direct-read exceptions are documented in
  code comments and in the author's report, which is enough given the `today` precedent

## Optional notes (not blocking)

1. The author's report asks "architect to confirm or offer service functions" for the four direct
   reads. My answer: no new service export needed now. If a second module ever wants "channel
   health during a week window" or "recipients by permission", that's the point to extract a shared
   function (candidates: `channels/service.ts` `unhealthyDuring(tx, ctx, window)`, a
   `tenancy/service.ts` `membersWithPermission(tx, ctx, permission)`); not worth doing preemptively
   for one caller.
2. `render.ts:282`'s empty-`{{channels}}` sentence traces to `market-watch.ts`'s `isPromotable()`,
   which allows an R1 item to promote via `blankBelowReorderPoint` alone with no `channels` — as
   already flagged by the reviewer and routed to round 2. Not re-litigated here per the task brief.
