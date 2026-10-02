---
name: project-t19-5-digest-web
description: T-19-5 weekly digest web build (wave 19) — routing convention, real gaps found live-testing against T-19-3/T-19-4, and the win-copy decision needing reconciliation.
metadata:
  type: project
---

Built 2026-09-28, T-19-5 (web-engineer, sonnet). `/digests` list + `/digests/$weekKey` detail,
Today card, Settings → Notifications, Account toggle, public `/unsubscribe` — against
`invai-contracts` 0.7.0's `digest.*` / `me.notifications.*` / `digest.ready`.

## Non-obvious facts for next time
- **New TanStack Router route strings error at typecheck until the route tree regenerates.**
  `pnpm dev`/`vite build` regenerates `src/routeTree.gen.ts` (it's a tracked, committed file, see
  `git log -- src/routeTree.gen.ts`). Write all new route files first, *then* run one `vite build`
  to regenerate, then typecheck — don't fight the transient "not assignable to FileRoutesByPath"
  errors before that.
- `AnyLink` (`src/components/any-link.tsx`) takes `to` + `search` as *separate* props, no `params`.
  For a contract field like `DigestAction.href` that's a combined `"/orders?view=overdue"` string,
  split it yourself (`indexOf("?")`, `URLSearchParams`) before passing to `AnyLink`/`Link`.
- `RECIPIENT_DELIVERABILITY`/`EMAIL_SKIP_REASONS`-shaped `Record<X, string>` lookup tables: import
  the *type* (`RecipientDeliverability`) not the const array, or biome's `useImportType` and a
  cascading `never` in the `Record<>` key break `t()`'s overload resolution in a confusing way.
- `src/lib/errors.ts` has **no** existing "try again in N seconds" message built from
  `RATE_LIMITED`'s `data.retryAfterSec` — a spec reviewer's non-blocking note assumed one exists.
  Build it locally in your own route file (same pattern as `shipping.tsx`'s `voidErrorMessage()`);
  don't go looking for a shared helper that isn't there.
- **Fixed as of T-A7 (2026-09-30, B-225):** `formatDay()`/`formatDate()`/`formatDateTime()`
  (`src/lib/format.ts`) now use a private `dateLocale()` (`i18n.language`-based, not the browser's
  default) — this bullet's old claim that they call `toLocaleDateString(undefined, …)` is stale,
  don't repeat it. `dateLocale()` itself still isn't exported, so a file that doesn't own
  `format.ts` needs its own 2-line copy (see `digest-copy.ts`'s precedent, or T-A7's
  `greetingDateLocale()` in `routes/_app/index.tsx`). T-A7 also added a repo-wide Vitest ban
  (`src/lib/date-locale-ban.test.ts`) on the raw `toLocaleDateString(undefined` /
  `toLocaleString(undefined` pattern, built on `import.meta.glob` raw-text import (no `@types/node`
  in this app, so no real `fs` scan).
- A contract field can be a genuinely free string with **no enumerated values and no spec copy**
  (`DigestInsight.templateKey` for the D8 "win" — only D1-D7 have Copy-table rows). Don't block on
  it; pick your own small set of keys with copy, add a generic fallback so an unmatched value never
  shows blank or a raw key, and flag the exact strings you chose in the report for the backend
  builder to reconcile (recorded in `reviews/T-19-1-web-engineer-r1.md` and
  `reports/T-19-5.md`, wave 19).
- Forcing a real digest for a live-exercise pass: `buildDigest(companyId, weekKey, now)` from
  `invai-backend/src/modules/digest/build.ts` is the module's own documented "manual/forced path"
  — no fixture needed, callable via a one-off `tsx -e`/script against a migrated DB copy.
  `lastCompleteWeek(todayYmd)` (`src/modules/digest/week.ts`) gives the right `weekKey`.
- `vite preview` for a browser pass needs `VITE_API_URL` set at **both** build and preview time
  (the CSP connect-src check runs on preview's config load too, not just build's) — see
  [[feedback_dev_csp_needs_build_preview]].
- Playwright's `chromium` isn't at `node_modules/playwright` in this pnpm layout; require it from
  `node_modules/@playwright/test` instead (which re-exports it) when writing a one-off screenshot
  script outside the `@playwright/test` runner.
