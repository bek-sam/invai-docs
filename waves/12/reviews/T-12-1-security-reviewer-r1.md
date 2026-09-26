# Review of T-12-1 (round 1) — internal admin routes co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `src/api/internal.ts`, `src/env.ts` (`secret()` helper), `src/api/app.ts` mount order | see findings |
| `pnpm typecheck && pnpm lint` (invai-backend) | clean |
| `pnpm vitest run src/api/internal.test.ts` (own DB/Redis) | passed, part of the 87/635 full-suite run |
| Live API on `PORT=3129` with an isolated DB/Redis and `INTERNAL_ADMIN_TOKEN` set: <br>`curl` no header → `404`<br>`curl -H "X-Internal-Token: wrong"` → `404`<br>`curl -H "X-Internal-Token: <right>"` on `/internal/dlq/failed?queue=sync` → `200` with real (empty) data<br>`curl` with right token on `/internal/does-not-exist` → `404`, identical shape to a global unknown path<br>`curl` on `/rpc/internal/dlq/failed` and `/api/v1/internal/dlq/failed` → `404` (route doesn't exist under either tenant surface)<br>`/health` response has no token/secret leakage | all as claimed in the report |
| Grep for `INTERNAL_ADMIN_TOKEN` outside `env.ts`/`internal.ts`/`.env.example` | none — not referenced by any web/floor code or `VITE_*`/browser-shipped config |

## Checklist (internal routes)
| Item | Result |
|---|---|
| Token compared in constant time | **Yes.** `tokenMatches()` (`src/api/internal.ts`) hashes both the given and expected token with SHA-256 before `timingSafeEqual`, so both inputs to the comparison are always fixed-length 32-byte buffers — this avoids `timingSafeEqual`'s own `RangeError` on length mismatch (which would otherwise leak length, or crash) and removes any early-exit-on-length timing signal. The `!expected || !given` short-circuit before hashing only distinguishes "token feature is off" / "no header sent" from "wrong token", which is not tenant- or secret-dependent information. |
| 404 when unset | **Yes**, verified live and in `internal.test.ts` ("404s without the header, with a wrong token, and when the token is unset"). `INTERNAL_ADMIN_TOKEN` is wrapped in the shared `secret()` helper (`env.ts:16-21`), which makes it `.optional()` — so an environment that never set it boots fine and the routes fail closed, rather than the app refusing to start or (worse) accepting a falsy default. This is a deliberate, documented deviation from the card's "new required env var" wording, and it's the safer choice: a schema requiring the var would either break every existing `.env` or force a bypassable default. |
| Never tenant-reachable | **Yes.** `internal` is a separate `Hono()` sub-app mounted with `app.route("/internal", internal)` directly on the raw `app`, before and outside the `/rpc/*` middleware block and the `/api/v1` OpenAPI surface that exposes oRPC contract procedures. There is no contract procedure, permission, or `AuthMode` for it (matches `wave.md` stub A's rationale — no platform-admin tenant role exists). Confirmed live: the same path under `/rpc/` and `/api/v1/` both 404. A request under `/internal/*` never runs `buildContext`/`withTenant`, so a compromised tenant session gains nothing by hitting it — the only door is the header. |
| Route enumeration doesn't leak existence | **Yes.** `internal.all("*", notFound)` (the catch-all inside the sub-router, after `requireToken`) returns the identical `{"error":"not found"}` / 404 whether the path is wrong, the token is wrong, or the token is absent — checked live above. An attacker can't distinguish "route exists, bad token" from "route doesn't exist". |
| Payload minimization | **Yes.** `GET /dlq/failed` returns `companyId`, `attemptsMade`, `failedReason`, timestamps — not full job payloads, which the code comments note may carry PII (`outbox-relay.ts` "ids, names and errors only; payloads may carry PII" on `parkedOutbox()`). |
| Input validation on the mutating routes | **Yes.** `POST /dlq/redrive` and `POST /dlq/redrive-outbox` both parse the body through Zod (`Redrive`, `RedriveOutbox`) before use; a queue name outside `QUEUE_NAMES` or a malformed body returns `400`, not a crash or an unchecked query. `jobIds` is capped at 500 per call. |
| Blast radius of a leaked token | Bounded but real: the token grants cross-tenant read of every queue's failed jobs and the ability to redrive any of them or reset any parked outbox row, platform-wide — as designed (there is intentionally no per-tenant scoping for an operator tool). This is consistent with the card's explicit design (stub A) and is not a new risk introduced by the implementation; flagging only as a note for ops hygiene (rotate the token like any other operator credential), not blocking. |

## Blocking findings
None.

## Optional notes (not blocking)
- `redrive-outbox` resets `attempts` to 0 in addition to `dispatchedAt`, a deliberate extension over the card's literal route contract (documented in the report: "otherwise a redriven row re-parks after one more failure"). This only affects the row's own retry counter and doesn't touch payload contents or another tenant's data; not a security concern.
- Consider (future card, not blocking here): rate-limiting or audit-logging `/internal/dlq/redrive*` calls beyond the existing `log.warn` line, since it's a privileged, cross-tenant mutation path. Out of this card's scope (T-12-3 owns rate limiting).
