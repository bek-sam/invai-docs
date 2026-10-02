# Wave 19 — the weekly business review digest

**Dates:** 2026-09-27 to 28, pushed 2026-09-27 (per wave 18's push timing note).

## What was built
- **T-19-1** Digest contract (architect): a new `digest` procedure group, plus
  `digest.ready` realtime event and `me.notifications.*` preference fields.
- **T-19-2** Shared analyst queries + `digest_narrative` (ai-engineer): the digest's
  numbers and the assistant's analyst tools (from wave 17) now share one query layer
  instead of each reimplementing the same aggregations.
- **T-19-3** Digest module: schedule, snapshot, detectors, ranking, templates, deliveries
  (backend-engineer/digest): the engine that builds a weekly digest and decides what's
  worth surfacing.
- **T-19-4** Email infra: preferences, signed links, unsubscribe, mail headers
  (backend-foundation): the digest can actually be emailed, with a working one-click
  unsubscribe and no PII leaking through tokens, plus a fix for a rate-bucket bug (B-133).
- **T-19-5** Web: digest pages, Today card, settings, account toggle, unsubscribe page
  (web-engineer): the screens for all of the above.

## Why
The wave's own goal: every Monday, an owner or office user opens InvAI and finds "Your
week in review is ready" — last week's numbers (matching the profit page exactly), up to
3 ranked actions with a button each, one win, and a Market watch block (built on wave
18's market module), in English or Spanish, with the same digest by email for people who
opt in.

## What went wrong
- OrbStack (the local Docker runtime) hung for the first time this wave, and several
  agents and the tech lead stalled for 10-minute stretches that looked exactly like a
  usage-limit or model stall — every Postgres and Valkey call was blocking silently, with
  no error. This is the first of what becomes a recurring incident (it happens again in
  waves P4 and P6) — the fix: when agents stall, check `docker ps` first; if *that*
  hangs too, `orb stop && orb start` and bring the compose stack back up.
- Two separate round-2 fixes this wave turned out to be the exact same bug *shape*: web
  and backend disagreed on a key or name for one thing (the D8 "win" template key, cost-
  line names, an empty-channel case). Each side had been tested only against its own
  fixtures, with nothing comparing the rendered text to the backend's real wire values.
- The gate caught the sharpest bug of the wave: the digest told the owner to "stock before
  September" on September 28 — a season that had already passed — and showed an English
  date inside Spanish copy. No acceptance criterion had actually run the digest against
  *today's real calendar date* in both languages; every test had used a fixed, fake date.

## What the team learned
- When agents stall with no error, the first move is `docker ps`, not assuming a model or
  usage problem — this becomes a standing step in `run-golden-path`.
- Reviewers of cross-repo copy (web rendering something the backend computed) now grep
  both sides and compare keys directly, and any card that renders a backend fact includes
  one test against a real payload, not just each side's own fixtures.
- Date- and season-driven copy needs an acceptance criterion that runs against *today's
  real date*, in both languages — a fixed test date can hide a bug that only shows up on
  the actual calendar, which is exactly what reached this gate.

## Files to look at
- `invai-contracts/src/contract/digest.ts`, `src/schemas/digest.ts` — T-19-1.
- `invai-backend/src/modules/ai/analyst-queries.ts` — the shared query layer (T-19-2).
- `invai-backend/src/modules/digest/` — schedule, detectors, ranking (T-19-3).
- `invai-backend/src/lib/notify.ts`, `src/lib/links.ts` — email and unsubscribe (T-19-4).
- `invai-web/src/routes/_app/digests/`, `src/routes/unsubscribe.tsx` — T-19-5.
- `invai-docs/team/lessons.md` (2026-09-28, "Wave 19" rows, including the OrbStack and
  wrong-season findings).
