---
name: mock-asof-anchor-pattern
description: Pattern for computing "last complete period" asOf in market mocks without duplicating period.ts's ISO-week math
metadata:
  type: project
---

T-20-1 (wave 20, 2026-09-28) added `lastCompletePeriodEnd(granularity, now)` to
`invai-backend/src/integrations/market/mock.ts` to make `mockDemandSeries`'s `asOf` end at the
last *complete* ISO week/month, never a future date (gate issue 4). It deliberately does coarse,
midnight-UTC arithmetic (`isoDow = now.getUTCDay() || 7`, `midnight - isoDow*86_400_000` for
weeks; `Date.UTC(y, m, 0)` for months) just to pick which period to anchor the generated series on.

**Why it's still exact:** the actual `asOf` timestamp isn't derived from that coarse anchor. It
goes through `periodsEnding` → `isoWeek(d)` to get a period label, then `seriesAsOf`/`periodEndIso`
in `period.ts` (see [[period-iso-week]], already fixed for the Jan-4 anchoring bug) independently
recomputes the precise `23:59:59.999Z` end-of-period instant from that label. So a coarse "which
week" pick plus an exact "when does that week end" lookup is the right split — don't fold the
precise end-of-day math into `mock.ts`'s anchor function; it would duplicate `period.ts` and risk
the two drifting.

**How to apply:** when reviewing a future date/period hunk in `mock*.ts`, check it still delegates
the *exact* instant to `period.ts` rather than computing `23:59:59.999` itself, and that any new
"pick a period" helper stays private (not exported) since it's not part of the provider interface.
