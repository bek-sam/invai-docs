# Wave P1 — polish and bugs: test isolation, flakes, imaging, AI, thumbnails, floor QC banner

**Dates:** 2026-09-30 to 10-01.

## What was built
- **T-P1-1** Per-run test DB and Redis DB (B-228, absorbs B-215), market retry test on
  fake timers (backend-foundation) — the structural fix wave A2's lessons called for.
- **T-P1-2** Imaging polish (B-103 rest, B-41) plus a `/preview` thumbnail endpoint
  (imaging-engineer) — the backend piece T-P1-4 needed.
- **T-P1-3** AI and market polish (B-114, B-131, B-132, B-135, B-165, B-192) plus a
  publish-concurrency test (ai-engineer).
- **T-P1-4** Design and order-item thumbnails (B-209) (backend-engineer/catalog) — real
  thumbnails instead of placeholders in the catalog and on order items.
- **T-P1-5** Floor QC result banner in Spanish (B-222) (floor-engineer) — the Spanish QC
  result banner actually says what happened, not a blank or English fallback.

## Why
This is the first of a string of "P" (polish) waves that work through smaller, real bugs
filed as backlog items earlier in the project rather than new features — agents and the
gate running backend tests at the same time without wiping each other, real thumbnails
instead of placeholder art, and print-readiness checks (ICC, mirror, bounds) on sheets.

## What went wrong
- T-P1-1's own new unit test for the Redis-claim registry deleted and refilled the *real
  shared* claim list it was testing, because the test exercised the registry at its
  production location instead of an injected one — live parallel test runs elsewhere
  lost their claims while this test ran.
- T-P1-2's imaging work added new flag codes to an existing response, and the backend
  client's *fixed enum* rejected them — imaging's own unit tests stayed green the whole
  time, because nothing had run the real backend consumer against the changed provider
  response.
- A backend card (filling in a long-null design-preview field) made a list page fire about
  40 signed-URL requests at once the moment the field started getting filled — caught by
  E2E as aborted requests, but missed by the card's own review because the web screen that
  rendered the field wasn't listed on the card at all.

## What the team learned
- Tests of shared-infra registries (locks, claims, queues) use a unique injected prefix
  and never read, assert or delete global state — now in the `independent-review`
  checklist and modeled in `invai-backend/src/test/test-redis.test.ts`.
- A provider response change gets verified by running the real consumer client against
  the changed provider locally before review, not just the provider's own unit tests.
- When a backend card turns on data a web screen already renders, the card names that
  screen, and the reviewer loads it once with the network tab open (checking request
  count and aborts) — not just the backend's own test suite.

## Files to look at
- `invai-backend/src/test/global-setup.ts`, `src/test/test-redis.test.ts` — T-P1-1.
- `invai-imaging/app/main.py` (`/preview`) — T-P1-2.
- `invai-backend/src/integrations/imaging/client.ts` — the fixed-enum consumer gap.
- `invai-backend/src/modules/catalog/service.ts` — thumbnails (T-P1-4).
- `invai-floor/src/i18n/es.ts` — the QC banner fix (T-P1-5).
- `invai-docs/team/lessons.md` (2026-09-30/10-01, "T-P1-1 review", "T-P1-2 review", "wave
  P1 gate" rows).
