# Review of T-17-3 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: ai-engineer on claude-opus-5.5
- Verdict: approve

The backend tree was idle (HEAD at `97780c1`, clean working tree), so I ran directly against the
main checkout rather than a worktree, per the tech lead's note.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 5ee0453 --stat` / `show 97780c1 --stat` | 9 files then 5 files, all inside owned paths plus the three wave.md grants (S-33 in `assistant-tools.ts`/its test, `evals/baseline.json` assistant entry, `mock.ts` follow-up) |
| `pnpm typecheck` | `tsc --noEmit` clean |
| `pnpm lint` | `Checked 297 files … No fixes applied.` |
| `pnpm test` (own DB `invai_t173_review`, Valkey DB 14) | `Test Files 98 passed (98)`, `Tests 715 passed (715)` — matches the report |
| `NODE_ENV=test tsx evals/run.ts assistant --json` (own DB) | `Cases: 30  Plumbing 30/30 (100%)  Quality 17/17 (100%)`, by-tag counts match the report exactly (including the new `spanish`, `follow_up`, `business_review` tags) |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend 308d16f` (base = T-17-2's commit, so the diff covers exactly T-17-3's two commits) | 2 hits, both reviewed and non-blocking (below) |
| Live 2-turn exercise: API on `:3152` (mock provider), `owner@desertbloom.test`, "How did this week compare to last week?" then "And only Etsy?" in the same conversation | turn 2's `tool_call` is turn 1's exact `compare_periods` input plus `"channel":"etsy"`; server log shows `historyTurns:0` on turn 1 and `historyTurns:2, toolLines:[["compare_periods"]]` on turn 2 |
| `grep -n "S-33" invai-docs/security/v1-review.md` | confirms S-33 is a real, pre-existing filed finding (not invented in this report), now marked **Fixed** citing this commit and the security-reviewer's own round-1 approval (`T-17-3-security-reviewer-r1.md`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `toolMemoryLine` test: exact compact line, hostile-summary neutralization verified by hand (see below), 600-char cap verified (`long?.length === TOOL_LINE_MAX`); end-to-end test shows turn 2's `history[1].text` starts with the tool line and the turn-1 buyer email is scrubbed; 20-message limit untouched (`.limit(20)` not touched in the diff) |
| 2 | yes | `assistantSystem(run)` puts the cached prefix at index 0 with `cache_control`, context (if any) at index 1 with none; the test does a real `Buffer.from(...).equals(...)` byte comparison across two shops (Phoenix vs Madrid) in addition to `toEqual`/`toBe` — genuinely proves byte identity, not just "looks equal" |
| 3 | yes | prompt text checked for the language rule; eval cases `as-027` (Spanish orders question) and `as-030` (Spanish business review) exist and ran (informational quality in mock mode, as expected — no key) |
| 4 | yes | prompt test asserts "Call independent tools in the same turn", "at most 3 recommendations", all four Finding/Evidence/Action/Expected-impact labels plus "Estimate", the honesty-rule phrases, and that nothing per-shop or dated leaks into the cached text (`not.toMatch(/\d{4}-\d{2}-\d{2}|America\//)`) |
| 5 | yes | `ASSISTANT_PROMPT.version === 4`, `ASSISTANT_MAX_ITERATIONS === 10`, wired into `anthropic.ts`'s `max_iterations` |
| 6 | yes | `mock.ts`'s deterministic routing is untouched by `5ee0453`; the 17 deterministic eval cases still pass at 17/17 |
| 7 | yes | 30/30 plumbing, 17/17 deterministic quality, 4 new cases added (Spanish, follow-up, 2×business-review), baseline refreshed for the assistant route only |
| 8 | yes | the `if (e.name !== "get_production_status")` guard is gone; `AssistantToolName` is now derived from the contract's own `AssistantEvent` type (`Extract<AssistantEvent, {type:"tool_call"}>["name"]`) instead of the old `as "get_profit"` cast, and a test parses every real tool name from `assistantTools(ctx)` against `AssistantEvent.safeParse` |

## S-33 (range cap, all 8 ranged tools) and the follow-up grant
- `rangeProblem`/`rangeRefusal` run inside the shared `t()` wrapper, so the check applies structurally to every tool with `from`/`to`, not per-tool — I confirmed by reading `assistantTools()`'s `t()` helper that `get_stock` and `get_production_status` (no range input) are correctly unaffected (`rangeProblem` returns `null` when both sides of a pair are `undefined`).
- Hand-verified the exact-400-days boundary in the test (`2025-05-11` → `2026-06-15`) really is 400 days (234 remaining days of 2025 + 166 days into 2026 = 400), and the check uses strict `>` against `MAX_RANGE_DAYS * 86_400_000`, so exactly 400 days is correctly allowed while 400+ε is refused.
- The test list covers all 8 ranged tools by name (`get_profit`, `get_orders_summary`, `get_listing_performance`, `get_channel_performance`, `compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health`) and separately checks `from >= to`, an unparseable date, and an oversized `previousFrom`/`previousTo` on `compare_periods`.
- The refusal is a normal `ToolOutput` (`data.error`), not a throw — matches the report's stated reason (a thrown error after the `tool_call` event was already streamed would leave the UI chip without a result, and the mock provider calls tools directly). This is the right shape for a recoverable, model-actionable error.
- Follow-up mock logic (`planFollowUp`) only fires when the new message matched no tool keywords, re-derives the tool set by re-planning the **original literal user question** (not the assistant's tool-line text or any tool result), and only ever narrows that independently-derived set — a hostile tool `summary` embedded in a design name could at most inject an extra name into the `used` filter set, which can only *remove* candidate tools from `base`, never add a tool that keyword-matching didn't already select. No privilege-escalation path found; this is mock/demo routing only (not the real model), so I'm not blocking on it, but it's worth security-reviewer's eyes if not already covered (their round-1 file at `T-17-3-security-reviewer-r1.md` already covers S-33; unclear if it looked at `planFollowUp` specifically).

## Blocking findings
None.

## Test-weakening scan, reviewed
1. `vi.spyOn(mockProvider, "assistant").mockImplementation((run, onUsage) => { runs.push(run); return real(run, onUsage); })` — a passthrough spy on the **mock provider** used only to capture the `AssistantRun` object for inspection (byte-identity and tool-memory tests); it calls through to the real mock implementation, so `svc.ask`, `shopContext` and `toolMemoryLine` (the units under test) are never mocked. Not a weakening.
2. One assertion removed in `assistant-tools.test.ts` (`.rejects.toThrow(/before/)` for `compare_periods`), replaced immediately in the same file by two assertions in the same test (`error: "invalid_range"`, message match) plus a whole new `describe("S-33: range span cap")` block that checks the same and seven more tools. This is the intended behavior change from S-33 (throw → recoverable result) with materially *more* coverage after, not less. Not a weakening.

## Checks
- [x] Only owned/granted paths changed in both commits
- [x] Nothing outside scope
- [x] Tests exercise the behavior; weakening scan hits reviewed and explained above; both new/changed tests are additive or strictly stronger
- [x] Tenancy — no new tables or queries outside the tenant boundary; `shopContext`/`toolMemoryLine` read only derived, non-PII shop data (time zone, channel labels, currency); `gateway.ts` runs `context` through the same `stripPii`/`sanitizeText` pipeline as `message`/`history`
- [x] PII: connection names (free text) are explicitly excluded from the shop context (`connections[k].name` never read into the string, only `CHANNEL_RULES` labels); the byte-identity test's fixture connection names ("secret connection name") are asserted absent from the context string
- [x] Idempotency — n/a, no side effects beyond the existing conversation-row writes
- [x] Decisions recorded (tool line inside the assistant turn's text, not a separate message, to keep the 20-message window and existing scrub path; shop context explicitly labelled "set by InvAI, not by the user")

## Optional notes (not blocking)
- `evals/**` remains outside `tsconfig`/`biome` includes (pre-existing, already noted on T-17-2's review); unchanged by this card.
- A real-key eval run (Spanish quality, follow-up quality, business-review recommendation structure, cache-hit rate with the two-block system) is honestly flagged as owed in "Known gaps", correctly routed through the tech lead to the owner rather than run without a key.
