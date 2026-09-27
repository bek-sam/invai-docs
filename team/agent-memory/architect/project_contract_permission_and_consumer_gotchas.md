---
name: contract-permission-and-consumer-gotchas
description: Facts that bite contract design and plan reviews: which permission means "any member", owner-only permissions, web realtime map needs a case per new event, a stub per touched namespace, API vs web public URL envs
metadata:
  type: project
---

- "Any signed-in member" = permission `org.read` (every role incl. vendor holds it). `none` is reserved for the five auth-bootstrap procedures; `contract.test.ts` enforces the exact list.
- `billing.manage`, `org.export`, `org.delete` are OWNER_ONLY in `roles.ts` (a bare admin lacks them). When a spec says "owner/admin", the permission is `billing.read` / `org.manage`, not `billing.manage`.
- A new `RealtimeEvents` entry refreshes nothing in web until `invai-web/src/lib/realtime.ts` `keysForEvent` gets a `case` (the switch ends in `default: []`). Put that file in the web card's owned paths up front. Floor does not consume `RealtimeEvents`.
- Adding a key under an existing namespace (e.g. `me.*`) breaks backend typecheck in that module's router (`authed.me.router` in `modules/tenancy/router.ts` must implement it), not only `src/api/router.ts`: plan one stub commit per touched namespace.
- Env: `BETTER_AUTH_URL` is the API's public origin, `WEB_ORIGIN` the web's; signed public links need no new `PUBLIC_*_URL`.
- The oRPC `rateLimit` middleware (`api/orpc.ts`) buckets per company (`ai|auth|reads|writes`); a per-user "once a minute" rule needs its own Redis key in the handler.

**Why:** found in the wave 19 plan review (2026-09-27); each would have forced a mid-wave grant or a wrong permission.
**How to apply:** check these before approving a plan's interface table or designing a new namespace.
