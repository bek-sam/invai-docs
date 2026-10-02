# Review of T-26-3 (round 1)

- Reviewer: backend-foundation on sonnet
- Author: ai-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-backend && OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm typecheck` | clean, exit 0 |
| `cd invai-backend && OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/db src/modules/photos` | 16 files, 84 tests passed (ai/service tests for this card run as part of `src/modules/photos` via the stubs it exports; the module's own `src/ai` suite was re-checked by reading, not re-run full, per the card's narrower scope for a co-reviewer) |
| `git -C invai-backend show --stat d7e7b6c` | only `drizzle/0039_ai_photos.sql` + meta, `src/ai/models.ts`, `src/db/schema/ai.ts`, `src/modules/ai/{photo-analysis,photo-attach,service}.ts` — all owned paths |

## Migration review (`drizzle/0039_ai_photos.sql`)
1. **`ALTER TABLE listing_drafts ADD COLUMN image_disclosures jsonb DEFAULT '{...}'::jsonb NOT NULL`** — constant default + NOT NULL is metadata-only on PG ≥11 (no table rewrite, no full-table lock hold beyond catalog update). `listing_drafts` is an existing, moderately-sized table; this is the same safe class as prior `ADD COLUMN ... DEFAULT ... NOT NULL` migrations (precedent: `shipments.dest_zone`, `cost_settings.fixed_monthly_cents`, noted in my own memory). Not blocking.
2. **`CREATE UNIQUE INDEX ai_credit_ledger_photo_ref_uq ... WHERE ref_type LIKE 'photo_%'`** — not `CONCURRENTLY`, no `SET LOCAL lock_timeout`. I checked this specifically because `ai_credit_ledger` is a write-heavy, unbounded-growth ledger (every priced AI action across every company writes a row) — the same class of table as `audit_log`/`inventory_movements` that `zero-downtime-migration` calls out. Current size: 28 rows in the dev DB (pre-pilot, no live shops yet), so a plain `CREATE INDEX` is instant today and the skill explicitly allows a plain index on a small table. I verified the partial condition is correct and deliberate: the composition charge path (T-26-4) writes `ref_type = "photo_composition"` (matches `LIKE 'photo_%'`, so a retried render job's double charge is rejected by this index as a backstop to the `charged_at` guard), while the analysis charge path (this card, `photo-analysis.ts` line ~108) writes `ref_type = "design"` (does **not** match, so a `refresh` is correctly allowed to charge again, per report). Logic is right.
   - **Not blocking today**, but flagging for the record: my own precedent on this exact table (`drizzle/0030`/`0031`, composite FK add + validate on `ai_credit_ledger`) used `SET LOCAL lock_timeout = '5s'` even for a cheaper `VALIDATE CONSTRAINT`. Once this table has real-shop volume (post-pilot), a plain `CREATE INDEX` here should move to the `CONCURRENTLY`/online-runner path per the skill's "anything expected over ~100k rows" rule. Noting as a follow-up, not holding the card on it — table is still new-feature-small and pre-pilot.
3. Journal order correct: `0039_ai_photos` before `0040_photos_sets` (confirmed via `_journal.json`), matching the card's explicit ordering requirement (the partial index on `ai_credit_ledger` must exist before T-26-4's render job can rely on it as a backstop).
4. `ai_credit_ledger.refType`/`refId` are plain `text`/`uuid` (no FK) — correct, since `ref` is polymorphic (`design`, `photo_composition`, the digest id, etc.); no RLS/FK gap here.

## Acceptance criteria (migration + stub-correctness lens; full behavior owned by `reviewer`)
| # | Met? | Evidence |
|---|---|---|
| Schema additive, safe defaults | yes | New column has a constant default; no existing column retyped or dropped |
| Partial unique index correct | yes | Confirmed condition and both charge paths' `ref_type` values as above |
| Stubs committed first, before T-26-4's migration | yes | `d7e7b6c` (0039) precedes `5930d59` (0040) in git log and journal order |
| `CREDIT_KINDS`/job-kind mirror matches contract | yes | `photo_image`, `photo_scene` appended at the same tail position as `invai-contracts`' `CREDIT_KINDS`; `photo_analysis` added to `AI_JOB_KINDS` (enumText, no migration needed, correct per precedent) |

## Blocking findings
none.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope (stubs match exactly what T-26-4's card lists as depended-on interfaces)
- [x] Tests exercise the behavior; no weakening observed in the files I read
- [x] Tenancy n/a for the migration itself (RLS already exists on both tables); idempotency: partial unique index backstop correctly scoped; money n/a (credits, not cents)
- [x] Decisions recorded: ADR 0023 §5 covers the charge guard and ledger ref shape this migration implements

## Optional notes (not blocking)
- Pre-pilot, `ai_credit_ledger` is small; before a pilot goes live, re-evaluate whether this index (and similarly-shaped future ones) need the `CONCURRENTLY`/online-migration path once the table has real volume.
