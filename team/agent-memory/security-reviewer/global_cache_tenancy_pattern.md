---
name: global-cache-tenancy-pattern
description: How to judge a global (no company_id) table for cross-tenant leaks, and the specific check for "what gets fetched" vs "what gets validated on write"
metadata:
  type: project
---

InvAI allows exactly one global table without `company_id` per ADR at a time (CLAUDE.md rule 7 is
enforced by `invai-backend/src/db/rls-coverage.test.ts`'s `PUBLIC_READ_TABLES` set). Precedent:
`trademark_marks` (no tenant column, `publicReadPolicy()` + `.enableRLS()`, `invai_app` gets
SELECT only, filled via `withSystem`). ADR 0015 added `market_series_cache` on the same pattern
(2026-09-27, T-18-1, reviewed in `invai-docs/waves/18/reviews/T-18-1-security-reviewer-r1.md`).

When reviewing a new global/public-read cache table:
1. Check the columns literally have no tenant id, connection id, user id or free text — only
   fixed/enumerated values (e.g. taxonomy keys), never a value a shop could inject.
2. Check RLS matches the `trademark_marks` shape exactly: `publicReadPolicy` + `.enableRLS()`,
   app role SELECT-only (no INSERT/UPDATE/DELETE), writer is `withSystem` with a comment.
3. **Check what the refresh/write job *fetches*, not just what it's allowed to *store*.** An ADR
   can correctly validate that every stored row is a canonical/taxonomy value, while staying
   silent on whether the job decides *which* values to fetch by looking at tenant data (e.g.
   "only fetch niches some tenant currently uses"). That selection step, if tenant-driven, turns
   row presence/freshness into a low-fidelity cross-tenant inference channel even though the
   table itself has zero tenant columns. The safe pattern is: iterate the *entire* fixed key
   space every run, unconditionally, so presence/freshness never correlates with any tenant's
   usage. Look for this explicitly in the ADR's write-job description; if it only describes
   validation of what's stored, treat the fetch-selection question as a real (if Low severity)
   gap and file it rather than assume the safe interpretation. Check the spec too — it may
   already direct the safe behavior even if the ADR doesn't restate it (market-signals spec did:
   "one fetch per (canonical query, source) for all shops").
4. This is Low severity, not High, when the only leakable fact is aggregate/non-identifying
   (e.g. "some shop uses niche X") — no company, buyer or order data. Don't escalate it to the
   owner; file it as a normal finding (S-34) with an owner and let the next card close it.
