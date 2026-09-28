# 0016: Email links are signed `/l/:token` routes outside oRPC; per-person email preferences are keyed by kind and opt-in only

- Status: accepted (2026-09-27; agreed in the wave 19 plan review, `waves/19/reviews/plan-architect.md` A1, A9)
- Type: architecture

## Context
- The weekly digest (`specs/weekly-digest.md`, ADR 0014, OI-7) is the first feature that emails a
  person a link they act on without a session: RFC 8058 one-click unsubscribe (`List-Unsubscribe-Post`)
  and action clicks. Every oRPC procedure in `invai-contracts` needs a Better Auth, floor or station
  session (`contract/_base.ts` `AuthMode`; `public` exists but nothing uses it), and a mail client
  or link scanner sends neither a session nor an RPC body.
- Link scanners follow GETs. Spec pipeline 13: GET must never unsubscribe; only POST does.
- The API origin serves `default-src 'none'` CSP, so it cannot render a confirm page; the web
  (`WEB_ORIGIN`) already renders public routes.
- A token must be bound to shop + person + purpose (spec AC25): an unsubscribe token for shop A
  edited to a person in shop B changes nothing in either shop. `src/lib/crypto.ts` already has
  `signPayload`/`hmacHex`; `BETTER_AUTH_SECRET` is the only signing secret in the environment and a
  purpose-bound derived key avoids a new env var and a new rotation story.
- Email is opt-in per person (owner guardrail, spec open question 1). A single `digestEmail`
  boolean on the user would need a schema change for every future kind (production week,
  monthly review), and an admin turning someone's email *on* would defeat opt-in.
- Links: card T-19-1 (architect), T-19-4 (backend-foundation, implementer), T-19-5 (web-engineer,
  unsubscribe page), wave `waves/19/wave.md` A1/A9, spec `specs/weekly-digest.md` AC23–AC25.
  Decided by the architect; co-reviewed by backend-foundation and web-engineer on T-19-1;
  security-reviewer reviews the implementation on T-19-4.

## Decision
1. Links in email are plain HTTP routes on the API origin, `${BETTER_AUTH_URL}/l/:token`,
   implemented in `invai-backend/src/api/links.ts`, not oRPC procedures. Their URL shape, token
   payload, methods and status codes are pinned in `invai-contracts/README.md` ("Public link
   routes (not oRPC)") and change only through a new payload version `v`.
2. The token is `signPayload` with the purpose-bound key `hmacHex(BETTER_AUTH_SECRET, "links:v1")`
   and payload `{ v: 1, k: "unsubscribe" | "click", c: companyId, u: userId, r: ref (<= 128 chars),
   exp }`; unsubscribe expiry 400 days, click 30 days. The verifier binds `c` + `u` to an active
   membership before acting. Tokens never appear in logs.
3. `POST /l/:token` is the only mutating method and only for `k: "unsubscribe"` (`click` -> 405):
   idempotent, sets the person's preference off with source `unsubscribe_link`, 200 on repeat;
   `{ "undo": true }` on the same token is allowed within 24 h of that unsubscribe, else 409.
   `GET /l/:token` never mutates: it redirects to `${WEB_ORIGIN}/unsubscribe?token=…` or, for a
   click, to a same-origin path (`/` if the handler's path is not a plain `/path`). Invalid or
   expired: GET -> `${WEB_ORIGIN}/unsubscribe?error=invalid`, POST -> 400. Per-IP `links` bucket,
   60/min.
4. Per-person email preferences are keyed by kind: `NOTIFICATION_KINDS` in
   `invai-contracts/src/schemas/tenancy.ts` (`["digest"]` in 0.7.0, values appended at the end),
   default off, with `source: settings | unsubscribe_link | admin`. Only the person turns a kind on
   (`me.notifications.set`, `org.read`); an admin (`digest.settings.setRecipientEmail`, `on:
   false` by type) or an unsubscribe link can only turn it off.
5. Send idempotency lives in one place: `sendUserEmail` (`invai-backend/src/lib/notify.ts`) with a
   durable `email_sends` row per `(company_id, dedupe_key)`; a repeat key returns
   `{ status: "skipped", reason: "duplicate" }`. Feature modules record their own per-recipient
   outcome row (the digest's `digest_deliveries`) but never re-implement the send guard.

## Consequences
- Easier: any future email kind (production week, monthly review) reuses the routes, the token
  format, the preference table and the send guard by adding an enum value; no new auth mode or
  contract procedure. Link scanners cannot unsubscribe anyone. No new secret to rotate.
- Harder: two public, auth-less endpoints exist on the API origin; they are rate limited per IP
  and every change to `src/api/links.ts` gets a security-reviewer co-review (auth flag). A rotated
  `BETTER_AUTH_SECRET` invalidates every link in every inbox; the unsubscribe page then says to sign
  in and use Settings, which stays a working path.
- Enforcement: `invai-contracts/src/digest.test.ts` (kinds, sources, `on: false` by type);
  T-19-4's tests for AC24 (POST twice, GET mutates nothing) and AC25 (cross-shop token rejected);
  `src/api/security.test.ts` (security-reviewer) for the auth-less routes.
- Follow-up owners: backend-foundation (routes, `notify.ts`, `email_sends`), web-engineer
  (`/unsubscribe` page with Undo), tech lead (link this ADR from `waves/19/wave.md`).
