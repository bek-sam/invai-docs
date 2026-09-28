---
name: gate-traps
description: Non-obvious traps when running the wave integration gate (run-golden-path): the shared ai rate bucket breaking a full pnpm e2e, screenshot timing, guard-hook limits on kill, zsh echo, SSE curl shape.
metadata:
  type: project
---

- 2026-09-27 wave 18 gate: a full `pnpm e2e` in invai-web on a fresh seed trips the per-company `ai` rate bucket (20/min, `RATE_BUCKET_LIMITS.ai`; `bucketFor` in `invai-backend/src/api/orpc.ts` sends every `ai.*` path there, including `ai.credits.balance/ledger` and `ai.assistant.conversations`). Symptom: the market.spec vote test shows "Something went wrong: Too many requests" (its own error message blames the seed), then screens.smoke fails on `/settings/billing` with a 429 on `ai/credits/ledger`. Each suite passes alone.
  **Why:** the bucket was sized for model calls, not for the reads the assistant page makes on every ask and reload. Filed in the wave 18 gate (owner backend-foundation/architect).
  **How to apply:** until fixed, run `market.spec.ts` and `screens.smoke.spec.ts` a minute apart and report the full-suite result honestly; count `/rpc/ai/*` statuses from `trace.zip` (`*.network` JSON lines, `resource-snapshot` entries) for evidence.
- Gate screenshots: wait ~3 s after `settled()` before shooting Today (KPI skeletons) and Profit (Recharts bars animate from 0, so they look tiny against a correct axis). Both looked like number bugs and were not.
- Spanish vote buttons on the assistant: the aria-label ends "como que no sirve" (`market.vote.notUsefulAria`), not "no me sirve"; `market.spec.ts`'s es test never asserts vote cards because the trending starter has no recommendations on the seed.
- The guard hook blocks any single command that both runs `ps ... | grep` and `kill`. Kill recorded PIDs and `lsof -ti :<port>` in one command; do read-only `ps` checks in a separate command.
- In zsh, `echo =====` fails ("not found"): a word starting with `=` is expanded. Use `echo "----"`.
- Assistant SSE via curl: `POST /rpc/ai/assistant/ask`, body `{"json":{"message":"..."}}`, `-N`, `accept: text/event-stream`; events are `data: {"json":{...}}` lines. `tool_result` events carry `sources`/`recommendations`/`mock` at the top level (no `result` field).
- The worker's `market-sweep` job scheduler fires within a minute of a fresh worker start, so a fresh seed has market rows without running jobs inline.
- 2026-09-28 wave 19 gate: `settled()` in `invai-web/e2e/helpers/ui.ts` waits for the app shell, so it fails on the public `/unsubscribe` page and on Mailpit (`localhost:8025/view/<id>`); shoot those with a plain `waitForTimeout`.
- 2026-09-28 wave 19 gate: digest actions render as **links** ("Ship 13 overdue orders"), each with two buttons "Helpful: <action>" / "Not helpful: <action>", and Market watch items have "Mark '<text>' ..." vote buttons. Counting buttons by verb over-counts (10 for 3 actions); count `getByRole("link", { name: /^(Ship|Reconnect|Review|List|Reorder)\b/ })`.
- 2026-09-28: the market mock sources stamp `as_of` with the **end of the current ISO week** (Sunday), so on a Monday gate the digest/email shows "Google Trends, Oct 4, 2026" (a future date). Data, not a render bug; the web says "week ending Oct 4".
- 2026-09-28: `pnpm db:reset` doesn't flush Valkey, so a fresh worker replays stale BullMQ jobs (`ai.generateListingDrafts ... listing draft not found`, `final:false`). Noise, not a bug; grep the worker log for `digest`/`market` lines instead.
- 2026-09-28: scale runs on a private DB work with `TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/<db> TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/<db>` (global-setup creates and migrates it). Fixture inserts inside one `withSystem` are invisible from psql until commit, so a long run shows 0 rows while it works.
