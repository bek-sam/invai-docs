# Wave 1 — safe to put real keys in

**Dates:** 2026-09-24. **Pushed:** yes, after the gate passed with no failures.

## What was built
- **T-1-1** (backend-foundation): production refuses to boot on mock providers — `/health`
  in production has no `mocks` field at all, so nobody can accidentally ship on fakes.
- **T-1-2** (integrations-engineer): Shopify webhooks are verified *before* anything else
  happens. An unsigned or badly-signed `POST /webhooks/shopify` gets `401` and writes
  nothing to `webhook_deliveries` — the signature check runs ahead of storage, not after.
- **T-1-3** (integrations-engineer): supplier purchase orders can't let a tenant spend
  InvAI's own money by mistake (payments/migration risk — this card was still "planned"
  at the time wave 1's gate ran; see below).
- **T-1-4** (backend-foundation): staff invites work end to end — invite a teammate with a
  role, they get a real email in Mailpit, and accepting it locks their email and lands
  them on the right role's screen.
- **T-1-5** (ai-engineer): a brand-new production database has its reference data (trademark
  marks, plans) the moment `db:migrate` finishes, before any seed ever runs.

## Why
This is the first wave after the v1 golden path worked end to end on mocks only. "Safe to
put real keys in" means: once an owner adds a real Shopify or Stripe key, the platform
must not keep behaving like a demo. Before this wave, nothing stopped a webhook replay
attack, nothing stopped production from quietly running on fakes, and there was no invite
flow at all.

## What went wrong
- Nothing failed in the gate itself — the wave 1 gate (`waves/1/gate.md`) reports **no
  failures, no test retried, skipped or loosened**. This is one of the few waves with a
  completely clean first pass.
- The gate did flag a *process* risk, not a product one: three wave 2 stub commits had
  landed on top of wave 1's commits in the shared trees before the push, and no wave 1
  review covered them. The gate recommended pushing only up to the wave-1-only commits
  unless the tech lead confirmed the stubs were meant to go out together — an early
  example of commits from the *next* wave bleeding into a gate that was only asked to
  judge the current one.
- `team/lessons.md` records two foundational mistakes from this wave that shaped every
  wave after: a card's commit nearly swept up another agent's staged deletion because
  several agents share one git index (`git add <paths>` then a bare `git commit` commits
  everything staged, not just your paths), and a test DB failed with "relation already
  exists" after another card regenerated its drizzle migration (drizzle picks which
  migrations to run by the journal's timestamp, not a content hash, so regenerating one
  changes what every other test DB expects).

## What the team learned
- Commit with an explicit pathspec (`git commit -m ... -- <your paths>`) and check
  `git show --stat HEAD` afterward — promoted into the `respect-ownership` playbook.
- After a migration is regenerated, drop and recreate your own test DB, and coordinate
  migration regeneration through the tech lead rather than doing it solo — promoted into
  `zero-downtime-migration`.
- A gate judges the SHAs it was given, and flags (rather than guesses about) anything that
  landed on top of them mid-run — this habit shows up again in waves 5 and 7, where later
  gates found the *next* wave's commits already sitting on `main`.

## Files to look at
- `invai-backend/src/lib/env.ts` — the production/mock guard T-1-1 added.
- `invai-backend/src/api/webhooks.ts` — Shopify signature verification ahead of storage.
- `invai-backend/src/modules/tenancy/service.ts` and its invite email path (T-1-4).
- `invai-backend/src/db/seed/` reference data (marks, plans) applied on migrate, not seed.
- `invai-docs/waves/1/gate.md` — the full smoke-check table and the clean-pass evidence.
- `invai-docs/team/lessons.md` (2026-09-24, "Wave 1" rows) — the two git/migration lessons.
