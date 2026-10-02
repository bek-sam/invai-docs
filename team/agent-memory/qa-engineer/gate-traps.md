---
name: gate-traps
description: Environment and RPC-call gotchas that cost time during golden-path gate runs
metadata:
  type: project
---

Curl-testing oRPC directly (spot checks beyond the E2E suites) needs two things the E2E helpers hide:
- The body must be StandardRPC-envelope wrapped: `{"json": {...actual input...}}`, not a bare JSON object.
  A bare object gives `400 Invalid input: expected object, received undefined` even though the path resolved.
- Every request needs `x-contract-version: <value>` matching `invai-contracts` package.json version (check
  `node -e "console.log(require('./package.json').version)"` in invai-contracts), or floor/station requests
  get `426 CLIENT_TOO_OLD`.
- RPC paths use the router's dot-path (e.g. `shipping.scanForms.create` → `POST /rpc/shipping/scanForms/create`),
  not the `.route({...path})` REST annotation on the contract (that only applies under `/api/v1`, the
  OpenAPIHandler mount). Always POST for `/rpc/*` regardless of the contract's declared method.

**Why:** wasted several round-trips guessing at `/rpc/shipping/scan-forms/` (the REST-style path) before
finding the RPCHandler dot-path convention; same for the envelope and version header.
**How to apply:** when spot-checking any procedure not already covered by an E2E helper, wrap input in
`{"json": ...}`, add the contract-version header, and use dot-path segments for the URL.

Direct writes to the shared dev DB (even scoped, even to prove one acceptance case) are blocked by the
sandbox's "Modify Shared Resources" classifier — reads and refusal-proof inserts (that roll back or fail on
a constraint) go through, but an `UPDATE`/committed `INSERT` meant to seed a missing case does not. When an
acceptance case has no live example in the current seed (e.g. a populated inventory bin code), rely on the
reviewer's or author's own evidence for that case instead of trying to manufacture one directly in the DB.

A stale `dev:all` stack from an earlier gate attempt is normal at the start of a relaunch — always check
`lsof -iTCP:3000-3199` and the recorded PIDs before assuming ports are free; never touch a port not in your
own recorded list (e.g. :3142 belongs to another agent/session, leave it alone even if idle-looking).

Digest-dates browser tests (`e2e/digest-dates.spec.ts`, T-20-2 area) fail on a truly fresh seed because no
weekly digest exists yet for `/digests` to list — this is a known sweep-timing dependency (wave 20 gate
notes), not a regression, if it recurs on a wave unrelated to digests. Still failing at wave 23 as B-207
(AC1, Spanish heading shows an English weekday/month) even once a digest exists — don't count it as new.

`market.spec.ts:91` also needs setup on a fresh seed: known gap (wave-18 gate notes, filed to
backend-engineer/market) — `market.sweep` only enqueues `computeSignals` on a fresh seed, never
`refreshDemand`, until 03:00 UTC, so there's no "Sample data" badge. Force it once with a throwaway,
uncommitted `tsx` script under `invai-backend/src/scripts/__qa-*.ts` calling `refreshDemand()` then
`computeSignalsForShop(companyId, {}, deps)` (both from `src/modules/market/jobs.ts`/`compute.ts`, `deps`
= `integrationsMarket()` from `src/modules/market/deps.ts`); delete the script right after running it.
Same throwaway-script trick works for forcing `digest.spec.ts`'s prerequisite digest build when you don't
want the full opt-in+sweep+Mailpit flow in `digest-gate-flow.md`: call `buildDigest(companyId, weekKey)`
and `unsubscribeLink(companyId, userId, "digest")` (from `src/modules/digest/build.ts` /
`src/lib/notify.ts`) directly and mint `E2E_DIGEST_UNSUB_TOKEN` from the returned URL's `/l/<token>` part
— skips needing the email at all, at the cost of not exercising the opt-in/delivery path.

Wave-23 gate also found two real, still-open i18n bugs distinct from B-207: under `invai.lang=es`, the
Today-page greeting subheading date ("Tuesday, September 29") and an alert's body text ("Order N is past
its ship-by") stay in English while surrounding titles/labels are translated — different components than
the digest heading B-207 covers, so check both when doing an i18n pass. And systemically, no design or
order-item thumbnail ever renders (`image-off` placeholder everywhere, 40/40 on `/catalog/designs`):
`designs.list`'s placements always return `previewKey: null` — nothing populates it for designs (only
gang-sheet `previewKey` is seeded). Looked pre-existing, not caused by a reset.

## Note: earlier content lost this session, topics to re-derive
This file's content was accidentally overwritten in a 2026-09-29 session: an initial read used a wrong
absolute path (mistakenly tried `invai-docs/.claude/agent-memory/...` instead of the real
`invai/.claude/agent-memory/...`), got nothing back, and the file was rewritten from scratch without
re-checking. `MEMORY.md`'s index line for this file (not touched by the accident) still describes what was
here before; re-derive and re-add these rather than trusting a guess: full `pnpm e2e` trips the shared `ai`
rate bucket (find the per-tenant/per-route AI rate limit code and how many calls a full suite makes); a
screenshot-timing issue (probably a "wait for settle before screenshot" pattern); a kill/ps hook rule (check
`.claude/hooks/` for anything gating `kill`/`ps`); the Spanish vote button's aria-label locator; the shape of
an SSE response when curl-testing the assistant's streaming endpoint directly.
**Why noting this matters:** don't assume a memory file is empty/new just because a read returned nothing —
verify the exact path first (the true agent-memory root is `/Users/bekbolsun/invai/.claude/agent-memory/`,
never a path under `invai-docs`), since Write silently overwrites with no diff shown.
