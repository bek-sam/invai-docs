# Review of T-7-4 (round 1)

- Reviewer: reviewer on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git worktree add ../invai-backend-review-t74 0e16314` | clean checkout at `0e16314` (HEAD's uncommitted `shipping/service.ts` WIP excluded) |
| `git worktree add ../invai-contracts-review-t74 00bd3b3` (contracts pinned to last committed commit, to bypass another agent's uncommitted `ai.ts` edits that broke tsc via unrelated duplicate imports) | contracts clean |
| `node_modules/.bin/tsc --noEmit` | 0 errors |
| `node_modules/.bin/biome check .` | "Checked 267 files. No fixes applied." |
| `node_modules/.bin/vitest run` (own DB `invai_review_t74`, own Redis `/14`) | **79 files, 567 tests passed** — matches the report exactly |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t74 16ddc52` | "Result: no hits" (0 removed assertions, 74 added, no skips/mocks/loosened config) |
| Manual re-derivation of every 2026/2027 USPS date and every `shipby.test.ts` expectation by hand (day-of-week arithmetic) | all correct |
| `git diff --stat 16ddc52..0e16314`, `git show --stat 6caf8db`/`0e16314` | files listed below |

No `pnpm build` — this repo has no `build` step relevant to orders (it's `tsup` for the API/worker bundle; not part of this card's DoD checks beyond typecheck/lint/test). Did not spin up the API/worker or replay webhooks myself; the report's own webhook-replay evidence (4-step Shopify replay showing stale-skip and idempotent re-replay) is consistent with the code and I traced it through `updateExisting`/`handleWebhook` by hand instead of re-running it, per the token budget.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Postal holidays | Yes | `shipby.ts` `USPS_HOLIDAYS`; every 2026/2027 date checks out against the cited ELM/newsroom rules by manual day-of-week arithmetic (MLK, Presidents, Memorial, Labor, Columbus by formula; Juneteenth/Independence/Veterans/Christmas fixed-date, Sunday→Monday and Saturday-closes-that-Saturday handled per the cited July 4 2026 press release). `shipby.test.ts` new cases confirm Thanksgiving, Christmas+weekend, placed-on-holiday, and the 2027 Sunday-observed-Monday case, all hand-verified. |
| 2. Re-import bug | Yes | `updateExisting` now calls `computeShipBy` with `timeZone`/`processingDays`/`shipDays` threaded through (`import.ts:414-427`), so an unchanged CSV `ship_by` is a no-op; test `"skips Thanksgiving and re-imports an unchanged date-only ship_by as skipped"`. |
| 3. Staleness | Yes | `orders.channel_updated_at` (migration `0022`, additive, nullable). `updateExisting` returns `"stale"` when `sourceAt < o.channelUpdatedAt`; advances the watermark even on no-op reads. First-time orders (`channelUpdatedAt` null) skip the check and get it set on first apply — verified in `createOrder` and in `updateExisting`'s unconditional advance. Test `"ignores a payload older than the last one applied, even after a floor scan"`. |
| 4. Per-line cancel + holds | Yes, on the orders side | `cancelCheapest` filters `!isPressed(u)` before ranking, so pressed/packed/shipped/delivered units are structurally excluded from every cancel path (`applyLineEdits`, `cancelLineFromChannel`); pressed units always get flagged instead. `holdFromChannel` is keyed on `orderItemTransitions.data->>'channelSignal'`, one hold per signal per order, and won't re-apply a released hold. TikTok `On hold` and Amazon `is-buyer-requested-cancellation` are wired (see finding below on where). |
| 5. Line edits | Yes | Unrouted units (`imported`/`needs_mapping`) edited in place; routed units replaced new-then-old to avoid an all-cancelled gap; pressed units never touched, flagged `channel_edit_after_press` once per fingerprint via the audit-row lookup in `flagPressed`. |
| 6. Tests | Yes | `import-edits.test.ts` (11 cases, not 10 as the original report said — round 1 added the Walmart/hold tests), `shipby.test.ts` +3, `parse.test.ts` +2. Scan script found no weakening. |

## Blocking findings
1. `src/integrations/channels/csv/parse.ts`, `src/integrations/channels/types.ts` (touched in `0e16314`) — **out of the card's owned paths without a documented grant.** The card owns `modules/orders/**` and only the staleness hunk in `modules/channels/sync.ts`. `wave.md:131` is explicit that `integrations/channels/**` is "T-7-1's territory this wave, not T-7-4's," and recommends T-7-4 stop at the contract field/orders-side check and let T-7-1's integrations-engineer populate per-adapter signals. Round 1 instead has T-7-4 itself adding the Amazon/TikTok hold detection and the Walmart line-cancel split directly in the CSV parser. The report's own heading calls this "Round 1 (grants from the tech lead)," but unlike the identical situation on T-7-2 (`wave.md:143`, "Grant approved after the fact for the refund-ingest hunks in `channels/sync.ts` and the `ChannelRefund` type in `integrations/channels/types.ts`" — recorded in the build log), `wave.md`'s T-7-4 build-log entry (`wave.md:148`) records only the `shipsSaturday` and staleness-design approvals, not a grant to touch `integrations/channels/csv/parse.ts`/`types.ts`. Per the review rule, I can't approve on the author's word alone for a grant that isn't in the one place grants are recorded. Concrete scenario: if T-7-1's integrations-engineer is concurrently adding its own hold/cancel-signal plumbing to the same file (plausible, since wave.md assigned it there), the two land conflicting hunks with neither side aware of the other's shape for `ChannelHold`/`ChannelLineCancel`.
   - Not a functional defect: the diff is clean, tests pass, and the shapes match what `wave.md`'s stub anticipated. **Fix is procedural**, not code: tech lead confirms the grant and adds a `wave.md` build-log line for T-7-4 mirroring the T-7-2 precedent (or T-7-1 confirms it isn't touching these files this wave). I'd approve immediately once that's on record.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — **no**, see blocking finding 1 (`integrations/channels/csv/parse.ts`, `integrations/channels/types.ts`); everything else (`modules/orders/**`, `db/schema/orders.ts` + migration under the contracts/staleness-column grant, `modules/channels/sync.ts` hunk) is in scope.
- [x] Nothing outside scope — same caveat as above; no unrelated scope creep otherwise.
- [x] Tests exercise the behavior, and none were weakened (scan script: no hits; 0 assertions removed, 74 added)
- [x] Tenancy (`withTenant`, RLS on new tables) — no new tables; `orders.channel_updated_at` is a column on an existing tenant table, already under RLS. Idempotency: `holdFromChannel`/`cancelLineFromChannel`/webhook stale-skip all verified idempotent by re-reading (not just re-running the same command twice, but tracing the guard conditions). Money in cents: n/a to this card. en/es text: the two new hold notes (`"The buyer asked..."`, `"...has this order on hold..."`) are English-only user-facing strings on `orders.holdNote` — same pattern as existing hold notes in `service.ts`, so not a new gap this card introduces, but flagging as an optional note since it's buyer/office-facing text.
- [x] Decisions recorded where needed — staleness approach ("newest channel timestamp applied") recorded in `wave.md:148`; the missing item is the grant above.

## Optional notes (not blocking)
- `holdNote` strings added in `import.ts` (`holdFromChannel`) are English-only; worth a follow-up if hold notes are shown untranslated elsewhere in the UI.
- `channel_updated_at`'s "advance even on no-op reads" closes the X→Y→X gap the initial report flagged as a known limitation — good follow-through.
- Report's file-count for `import-edits.test.ts` says "10 cases" but I counted 11 `it(` blocks in the current file; harmless, just a stale number from round 0's report that wasn't updated for round 1's additions (`"cancels only the listed line's units..."`, hold tests).
