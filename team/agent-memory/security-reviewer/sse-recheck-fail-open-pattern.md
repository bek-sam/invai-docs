---
name: sse-recheck-fail-open-pattern
description: Review pattern for session re-checks on long-lived streams (SSE /events): buildContext swallows errors into anonymous, so check the probe, the connect path, and the client's loop teardown.
metadata:
  type: project
---

2026-10-01 T-P6-2/3: `buildContext` turns every error into an anonymous context and `isRevoked` fails open on Redis errors. Any code that treats "anonymous" as "revoked" (stream re-checks, 401-is-final clients) needs a DB-liveness probe or it locks every tablet on a DB blip.

**Why:** architect ruling C1 in `waves/P6/reviews/plan-architect.md`; the `/events` re-check got a `select 1` probe, but the connect path still returns 401 on a blip and the new floor treats a 401 at connect as final (relock, recover by PIN). Logged as Low optional notes in my r1 reviews, not yet a backlog row.

**How to apply:** on any card touching `src/api/events.ts`, `context.ts`, floor `sse.ts` or a client that stops on 401: (1) look for the probe on both re-check and connect paths; (2) check the client's teardown clears the token so the connect effect can't loop (`lock()` sets `session: null`); (3) a station-only token and anonymous must still get 401 at `/events` (I proved this with a throwaway test; `authz.test.ts` does not cover `/events`).
