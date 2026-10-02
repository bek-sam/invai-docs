# Wave P2 — P1 gate fixes, then the next polish items

**Dates:** 2026-10-01.

## What was built
- **T-P2-1** Catalog grid thumbnails load only on screen (web-engineer) — the direct fix
  for P1's 40-signed-URLs-at-once finding.
- **T-P2-2** Prove the floor scan timeout cause; imaging call out of the DB transaction;
  transient errors retry (B-233 part) (backend-engineer/catalog).
- **T-P2-3** `settled()` reports its timeout (qa-engineer) — the shared E2E wait helper
  now says *why* it gave up, instead of a bare timeout.
- **T-P2-4** Order drawer timeline states in the user's language (B-223) (web-engineer).
- **T-P2-5** Today actions build re-queues after 3 failed tries (backend-engineer/today).

## Why
Each card here is a named, numbered backlog item (B-233, B-223, etc.) rather than a new
feature — this wave's own goal is explicit: get a floor scan to never wait on background
thumbnail work, get the catalog list to load lazily, and pass one full gate with P1 and
P2 together before pushing.

## What went wrong
- T-P2-2 needed a full round 2: the card's job was literally to *find* why a floor scan
  was timing out, and the first pass hadn't isolated the imaging call (made inside a DB
  transaction, so a slow provider response held a database transaction open) from the
  transient-error path.
- A round-1 builder from this wave kept its own full-suite test runs going into round 2
  — held onto test Redis DB 15 — and the gate refused once as a result, because round 2
  was a different agent and nothing had told the round-1 agent to stop.

## What the team learned
- Before starting a round-2 builder on the same card, stop the round-1 builder and any
  of its background test runs first — now a standing step in the tech lead's gate
  checklist.
- A shared wait-helper (`settled()`) that times out silently is itself a source of wasted
  debugging time across every E2E spec that uses it — T-P2-3 makes it report *what* it
  was waiting for, which pays off immediately in later waves' root-causing.

## Files to look at
- `invai-web/src/routes/_app/catalog/` — lazy thumbnail loading (T-P2-1).
- `invai-backend/src/modules/catalog/service.ts`, `src/integrations/imaging/client.ts` —
  the transaction/timeout fix (T-P2-2).
- `invai-web/e2e/helpers/settled.ts` (or equivalent) — T-P2-3.
- `invai-web/src/components/orders/timeline.tsx` — T-P2-4.
- `invai-backend/src/modules/today/jobs.ts` — the re-queue-after-3-failures fix (T-P2-5).
- `invai-docs/team/lessons.md` (2026-10-01, "wave P2 gate" and "wave P2" rows).
