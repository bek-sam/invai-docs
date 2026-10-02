# Wave 3 — integrations hardened

**Dates:** 2026-09-25. **Pushed:** yes, all four cards approved.

## What was built
- **T-3-1** Shopify adapter complete (integrations-engineer): the real Shopify integration,
  reviewed by both security and compliance (webhooks, PII, marketplace policy).
- **T-3-2** EasyPost live tracking (integrations-engineer): real carrier tracking updates,
  verified the same way T-1-2 verified Shopify webhooks.
- **T-3-3** Listings and availability push (backend-engineer/inventory): stock levels push
  back out to the channel, not just in.
- **T-3-4** Heavy work to jobs (backend-foundation): anything slow (large CSV imports,
  batch labels) moves off the request path and onto the BullMQ job queue — the rule in
  `CLAUDE.md` ("heavy work goes to the job queue") made real.

## Why
Wave 1 and 2 made the platform safe to run with real keys and real money. Wave 3 makes the
integrations themselves trustworthy under real-world conditions: big CSV files that would
time out a request, webhook replay and signature attacks, and stock numbers that have to
stay in sync in both directions, not just on import.

## What went wrong
- The gate (`waves/3/gate.md`) passed clean — typecheck/lint/test/build green everywhere,
  DB migrate/seed cycle clean at migration 0014, API golden path 13/13, browser 15/15,
  floor suite green, and all five wave 3 smoke checks (batch labels, large CSV via the job
  path, three Shopify webhook behaviors, EasyPost's signature check, and the stock-push
  round trip) passed with evidence.
- The only issue was a cleanup detail, not a product bug: one orphaned `tsx watch`
  process survived an earlier restart and had to be found and stopped before the gate
  could certify a clean environment.
- `team/lessons.md` records a cross-cutting git problem from this wave: when several
  agents edit one shared file in one working tree, `git commit -- <path>` commits the
  *whole file*, including another card's in-progress hunks that happened to land between
  your diff check and your commit.

## What the team learned
- For a shared file touched by more than one card, stage only your own hunks (`git apply
  --cached` of your own patch) and commit from the index after `git diff --cached` shows
  only your changes — promoted into `respect-ownership`.
- The gate agent itself had been handing back mid-run every time it waited on a background
  job, forcing the tech lead to resume it repeatedly. The fix: a long-running gate polls
  with short sleeps inside its own turn and only hands back when it's actually finished —
  this habit is now baked into `run-golden-path`.
- This is the first wave where the gate explicitly confirms *zero* product code was
  touched during verification — every check driven through the running stack (curl, a
  small script using the same oRPC client the E2E suites use, and a real browser) rather
  than by editing `src/**`. That verification discipline becomes a standing expectation
  for every gate from here on.

## Files to look at
- `invai-backend/src/integrations/channels/shopify/` — the completed adapter (T-3-1).
- `invai-backend/src/integrations/carriers/easypost.ts` — live tracking (T-3-2).
- `invai-backend/src/modules/inventory/` and its availability push (T-3-3).
- `invai-backend/src/lib/queues.ts` — jobs for heavy work (T-3-4).
- `invai-docs/waves/3/gate.md` — the full clean-pass evidence and the orphaned-process note.
- `invai-docs/team/lessons.md` (2026-09-25, "Wave 3" rows).
