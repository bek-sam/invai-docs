---
name: fact-enum-text-no-migration
description: enumText() in invai-backend schema is a TS-only marker, not a pg enum/CHECK — adding a value never needs a migration
metadata:
  type: project
---

`enumText()` (`invai-backend/src/db/schema/_shared.ts:66`) just casts `{ enum: values }` for drizzle-kit's
TypeScript inference; the column stays plain `text()`. Adding a new literal to an array like `CREDIT_KINDS`
(`src/db/schema/ai.ts`) changes no DB constraint.

**Why:** T-18-4 round 2 added `market_niche` to `CREDIT_KINDS` under a grant that said "no migration". I
verified independently with `drizzle-kit generate --name <check>` → "No schema changes, nothing to migrate" —
don't take an author's "no migration" claim on faith, it's a 30-second check.

**How to apply:** when a card grants adding enum-like string literals to a `src/db/schema/*.ts` array, run
`drizzle-kit generate` myself in the review worktree before approving the "no migration" claim.
