# Review of T-19-1 (round 1)

- Reviewer: backend-foundation on Sonnet 5
- Author: architect on fable
- Verdict: changes-required

Scope of this review: co-review as backend-foundation, lens = can the backend (T-19-4 in particular)
implement this contract with existing foundation patterns, and does ADR 0016's link design match A9.
I do not re-judge digest business schemas (rank/detector/etc.) beyond what touches foundation concerns.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show e99ac21 --stat` | 16 files, matches report; working tree = e99ac21 (`git status --short` empty) |
| `cd invai-contracts && pnpm typecheck` | `tsc --noEmit` clean |
| `cd invai-contracts && pnpm lint` | biome: "Checked 55 files. No fixes applied." |
| `cd invai-contracts && pnpm test` | `Test Files 7 passed (7)`, `Tests 68 passed (68)` |
| `git -C invai-contracts diff --stat 378d6ae..e99ac21` | files touched: CHANGELOG.md, README.md, package.json, src/compat.ts, src/contract.ts, src/contract/digest.ts, src/contract/tenancy.ts, src/digest.test.ts, src/events.ts, src/index.ts, src/market.test.ts, src/realtime.ts, src/schemas/{ai,alerts,digest,tenancy}.ts — all within the card's owned-paths list (compat.ts/market.test.ts are the mechanical 0.7.0-bump follow-through the report names, standard architect territory) |
| `grep -n "finance.read\|org.manage\|org.read\|billing.read" src/roles.ts` | all four permissions pre-exist; `src/roles.ts` untouched in this diff — confirms AC1/AC2 add no new permission |
| Read `src/contract/digest.ts`, `src/contract/tenancy.ts` (notifications block), `src/schemas/tenancy.ts` (NOTIFICATION_KINDS/SOURCES), `src/events.ts`/`src/realtime.ts` diff | see findings below |
| Read `invai-backend/src/lib/ratelimit.ts` (existing token-bucket, `RateBucket`/`rateLimitKey`/`checkRateLimit`) and `invai-backend/src/db/schema/notifications.ts` (already drafted in the T-19-4 working tree: `notificationPreferences`, `emailSuppressions`, `emailSends`) | confirms implementability — see Foundation-fit findings |

## Acceptance criteria (foundation-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 1 additive, no new auth mode | yes | `digest` namespace and `me.notifications.*` are all `auth: user`; no new `AuthMode` |
| 2 permission matrix, no new permission needed | yes | `roles.ts` untouched; matrix test in `digest.test.ts` walks `PROCEDURE_PERMISSIONS`/`ROLES` |
| 5 `digest.ready` in realtime map, envelope carries org | yes | `src/realtime.ts` diff: `{digestId, weekKey}`, doc comment states "Scoped to the caller's org by the SSE stream, so no company id in the payload" — matches every existing realtime event's convention |
| 6 README pins `/l/:token` shape | present, but see Blocking finding 1 | README "Public link routes (not oRPC)" section |

## Foundation-fit findings (can T-19-4 build this with existing patterns, no new foundation module)

1. **Permission guard** — no new permission; `finance.read`/`org.manage`/`org.read`/`billing.read` are reused as-is. Nothing to add to the guard itself.
2. **`paginated()`** — `digest.list` uses `Page`/`paginated(DigestSummary)` from `../schemas/common`, the same helper every other list procedure uses. Fine.
3. **`withTenant`** — the public link routes carry `companyId` inside the signed token payload (`c`), verified before any DB access, then the handler runs under `withTenant(c, ...)`. This is the same shape as the existing floor station-token pattern (an unauthenticated-but-self-describing bound identity establishing tenant context), not a new mechanism. No foundation change needed beyond `src/api/links.ts` itself, which is T-19-4's own card.
4. **Realtime map** — `digest.ready` added to both `Events` and `RealtimeEvents` following the exact existing convention (org via envelope, not payload). No map-shape change needed.
5. **Rate limiter** — ADR 0016 §3 calls for a per-IP `links` bucket, 60/min, for an *unauthenticated* route. The current `invai-backend/src/lib/ratelimit.ts` token bucket (`checkRateLimit(bucket, companyId)`, `RateBucket = "auth" | "reads" | "writes" | "ai"`) is company-keyed by design (its own comment: "keyed by `company_id`, not IP"). Adding a `"links"` bucket keyed by IP is additive to `RateBucket` and reuses `rateLimitKey`/`takeToken` (the second argument is just an opaque string; the IP fits without changing the function signature). This is a small, in-pattern extension inside `src/lib/ratelimit.ts`, which T-19-4 owns — it does not require a new limiter mechanism. Flagging for the record since it's the first IP-keyed use of this bucket function; not blocking.
6. **New tables** — `notificationPreferences`, `emailSuppressions`, `emailSends` (already drafted in the T-19-4 working tree at `invai-backend/src/db/schema/notifications.ts`) are plain `add-tenant-table` shapes: `company_id`, `tenantPolicy()`, `.enableRLS()`, indexes leading with `company_id`. `NOTIFICATION_KINDS`/`NOTIFICATION_PREFERENCE_SOURCES` mirror the contract enums exactly. No new schema pattern.

**Conclusion on the lens question: yes, backend-foundation can implement T-19-4 (and the digest module can implement T-19-3) entirely with existing foundation patterns. Nothing here requires a foundation change beyond what T-19-4's own card already covers.**

## Blocking findings

1. **`README.md:137-138` (and `invai-docs/decisions/0016-signed-link-routes-and-notification-preferences.md:39`) — the pinned link-route spec contradicts itself on whether GET mutates.**
   The README states, in one bullet: *"`GET /l/:token`: never mutates."* — then, in the same sentence, for `k: "click"`: *"the registered handler records the click and answers 302..."*. Recording a click is a write. ADR 0016 point 3 has the identical shape: "`GET /l/:token` never mutates: it redirects... or, for a click, to a same-origin path" — it avoids saying "records" but still groups click-redirect under the "never mutates" umbrella while wave.md's spec pipeline 13 constraint ("GET must never unsubscribe") is narrower than "GET must never mutate anything."
   This is the exact inconsistency I was asked to check. T-19-4 is the one who has to turn this prose into code, and right now it says two different things: don't mutate on GET, and also mutate (record a click) on GET.
   **How it should read**, so T-19-4 and T-19-5 build the same thing: narrow the "never mutates" claim to the security-sensitive case only, and describe the click write for what it is:
   > `GET /l/:token` never changes a person's email preference or unsubscribe state — that only happens on `POST` with `k: "unsubscribe"`. For `k: "click"`, the GET *does* perform one write: it records the click, idempotently (same semantics as `digest.recordClick` — first click wins, a repeat is a no-op), purely for the `digest_action_click_rate` metric, before redirecting. This is intentional: RFC 8058 and link-scanner safety are about not letting an automated GET unsubscribe someone; a scanner recording a spurious click has no user-facing or destructive effect and costs nothing to repeat.
   Until this is reworded (in both the README and ADR 0016), an implementer reading only the "never mutates" line could reasonably build `GET` to also accept `k: "unsubscribe"` as a no-op-looking-but-actually-different case, or could build click-recording as non-idempotent — either way the two docs currently license two different implementations from the same sentence. This blocks because it's a pinned, security-relevant interface (auth-less route on the API origin) that changes only through a version bump per the ADR itself — it needs to say one consistent thing before T-19-4 codes against it.

## Checks
- [x] Only owned paths changed (`git diff --stat 378d6ae..e99ac21`) — matches card's owned-paths list
- [x] Nothing outside scope — contract-only change, no implementation, `Out of scope` respected
- [x] Tests exercise the behavior, none weakened — `digest.test.ts` is new (349 lines), asserts the full permission matrix, event shapes, enum tails; `market.test.ts` change only loosens a version-pin assertion to "at least 0.6.1" (intentional per report, so only the newest wave pins the exact `CONTRACT_VERSION` — not a weakening of behavior under test, just of which wave owns the exact-version assertion)
- [x] Tenancy / idempotency / money / en-es — N/A at contract level beyond schema shape; money in cents (`impactCents`), no PII in schemas, idempotency documented in doc comments for `feedback`/`recordClick`/`setRecipientEmail`
- [ ] Decisions recorded where needed — ADR 0016 exists but has the same contradiction as the README (see Blocking finding 1); needs a follow-up edit

## Optional notes (not blocking)
- `digest.ready`'s realtime doc comment explicitly states the envelope carries the org and the payload intentionally omits `companyId`, resolving the card-text-vs-wave.md discrepancy the report flags under "Decisions" — I agree wave.md's agreed interface governs per the card's own "Binding plan-review changes" clause.
- The IP-keyed `"links"` rate bucket (finding 5) is the first non-tenant use of `checkRateLimit`; worth a one-line doc comment in `ratelimit.ts` when T-19-4 adds it, so a future reader doesn't assume every bucket is company-scoped. Not a contract-card issue.
