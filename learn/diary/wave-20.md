# Wave 20 — digest and market copy that is right on today's date (wave 14, part 1)

**Dates:** 2026-09-28 to 29. **Pushed:** yes — contracts `78d2469`, backend `8ffff2b`, web
`d092a4b`, docs.

## What was built
- **T-20-1** Digest, market and Today copy on real dates (backend-engineer/market,
  digest, today): the exact fix for wave 19's "stock before September" bug — a season
  already past never gets prepare-for-it advice, and percent-point changes read as points
  ("+2.8 pts") instead of a bare, ambiguous number.
- **T-20-2** Web digest copy, permission errors and number format (web-engineer): a
  Spanish digest heading that's fully Spanish, one consistent Spanish number format, and
  a plain "You don't have access to this page. Ask the owner." instead of a raw
  permission error.
- **T-20-3** Side-effect and live-adapter tests (qa-engineer + backend-engineer/shipping
  as feature owner): 27 new tests proving every money or outside action (label buy, void,
  tracking push, stock push, listing publish, artwork render, supplier orders) has exactly
  one effect, even retried after a crash — each test shown to fail when its safeguard is
  removed.
- **T-20-4** Path guard for tech lead and reviewer, segment-aware push rule
  (platform-sre): the tech lead and reviewer agents can no longer edit code by mistake,
  and the push guard stops blocking safe pushes while still catching force-pushes and
  deletions.
- **T-20-5** Seed safe next to a running worker; stale jobs after reset (backend-
  foundation): the demo seed can rebuild while the background worker keeps running, and a
  reset clears old queued work so a reset doesn't leave the demo broken.

## Why
Wave 19's gate found that the digest, the assistant's market answers and Today could all
tell a shop to prepare for a season that had already passed, or leak a raw internal error
to an office user. This wave is the direct, dated fix — plus T-20-3's "one effect, even on
retry" test suite, which is the project's broadest single sweep of the idempotency rule
(`CLAUDE.md` rule 8) across every money-touching and outside-facing action at once.

## What went wrong
- Per the owner report: three usage-limit stops, two stalled agents, and one full disk
  (Docker stopped until restarted) — all recovered from disk with nothing lost.
- Three cards needed a second round, mostly because a copy example written into a card
  disagreed with an already-established rule about Spanish number formatting.
- A feature-owner reviewer (reviewing as a non-reviewer role) briefly edited a guard in
  product code to check a regression proof, then reverted it — the review prompt had said
  "read-only," but reviewing roles also build code day to day, and a regression proof
  looked like something that needed reproducing in place.
- QA and a builder hit missing `invai_app` database grants on a dev copy made with
  `createdb -T invai` — template copies don't carry the grants a later migration added.
- The gate surfaced a pre-existing deploy blocker (not new to this wave): in production,
  the browser's security policy would block file uploads to storage (B-190), filed for the
  deploy-readiness wave rather than fixed here.

## What the team learned
- Reviewers reproduce regression proofs only in a detached worktree, never in the shared
  tree — a "read-only" instruction to a role that also builds code needs this said
  explicitly, not implied.
- After copying the dev DB with `createdb -T`, reapply the grants from
  `drizzle/0001_grants_extensions.sql` on the copy before using it.
- Copy examples written directly onto a task card are still product copy — they get
  checked against existing formatting rules before the card starts, not caught in review.

## Files to look at
- `invai-backend/src/modules/{market,digest,today}/service.ts` — real-date-aware copy (T-20-1).
- `invai-web/src/components/digest/`, `src/lib/errors.ts` (`FORBIDDEN` case) — T-20-2.
- `invai-backend/src/modules/{shipping,inventory,ai,personalization,orders}/**
  *.acceptance.test.ts` — the 27 new idempotency tests (T-20-3).
- `invai-docs/team/hooks/guard-paths.py`, `guard-bash.py` (push segment) — T-20-4.
- `invai-backend/src/db/seed/` — the worker-safe, reset-safe seed (T-20-5).
- `invai-docs/waves/20/owner-report.md` — the full owner-facing account of this wave.
