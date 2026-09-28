# Review of T-19-5 (round 1)

- Reviewer: reviewer on sonnet
- Author: web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `node --version` | v24.21.0 |
| `pnpm typecheck` (invai-web) | `tsc --noEmit` — clean |
| `pnpm lint` (invai-web) | `biome check .` — "Checked 165 files in 176ms. No fixes applied." |
| `pnpm test` (invai-web) | `vitest run --passWithNoTests` — "Test Files 16 passed (16), Tests 88 passed (88)" |
| `VITE_API_URL=http://localhost:3000 pnpm build` (invai-web) | "✓ built in 1.84s", same pre-existing >500KB chunk warning (`env`/`index`/`BarChart`), not from this card |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | Only hits are in QA's `e2e/digest.spec.ts` (commit `5df9227`, `test.fail` placeholders per wave.md, not this card's commits) |
| `git -C invai-web diff --stat 5df9227..9b8a69e` | Every path matches the card's owned globs exactly (`routeTree.gen.ts` is TanStack Router's auto-generated file for the new routes) |
| Live: `PORT=3178` API against a fresh `invai_t19_rev_5` DB copy (already migrated to `bef6158`/`776697b`), Redis db 10, `WEB_ORIGIN=http://localhost:4478`, forced `buildDigest(companyId, "2026-W39", ...)` for Desert Bloom Tees | digest built `status: "ready"` |
| `digest.list` as presser (curl, cookie session) | `403 FORBIDDEN — Missing permission finance.read for digest.list` |
| `digest.settings.get` as office (curl) | `403 FORBIDDEN — Missing permission org.manage for digest.settings.get` |
| `digest.latest`/`digest.get`/`digest.recordClick` (x2)/`digest.feedback`/`digest.settings.get` as owner (curl) | Shapes match every field the components read; `recordClick` x2 returned the same `clickedAt` (idempotent) |
| `GET /l/:token` (signed unsubscribe token, curl -i) | `302` to `WEB_ORIGIN/unsubscribe?token=...`, `digest.settings.get` unchanged afterwards (no side effect) |
| `POST /l/:token` x2, then `{"undo":true}` (curl) | `{"ok":true}` both times (idempotent), then `{"ok":true,"undone":true}`; `digest.settings.get` reflected `emailOn:false` then back to `true` |
| Web: `VITE_API_URL=http://localhost:3178 pnpm build` + `vite preview --port 4478`, signed in for real via Playwright (owner and office) | 6 screenshots taken and looked at (see below) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Today card | yes | Screenshot: owner Today, en, 1440px, shows "Your week in review is ready" / "$0.00" / "See this week"; `digest.latest` returns `{digest:null,paused:false}` before a build → component renders nothing (code path `d?.status !== "ready" && !paused` → `null`); wired to `digest.ready` in `realtime.ts` (invalidates `orpc.digest.key()` + `orpc.today.key()`, same pattern as every other realtime case) |
| 2 Digest page | yes | Screenshot (es, 390px): glance grid, incomplete-orders warning, plan usage, actions section; live `digest.get` returned one D6 action (`ship_overdue`, n:78, href `/orders?view=overdue`) rendered as a button; `recordClick` called and idempotent; no market items in this build (`marketWatch: []`) so Market-watch reuse wasn't exercisable live, but the diff shows `RecommendationCard`/`SampleDataBadge` imported unmodified from T-18-5's files (`git diff --stat` shows zero changes under `src/components/market/**`) |
| 3 First-digest opt-in | yes | `today-card.tsx`/`$weekKey.tsx` show "Email me every week" when `me.notifications.get` reports `on !== true`; live screenshot of office Today shows the button (office hadn't opted in); `me.notifications.set({kind:"digest",on:true})` wired |
| 4 Settings → Notifications | yes | Screenshot: day/hour/timezone, AI-summary toggle disabled + shadow copy (live `aiSummaryMode:"shadow"` from the backend), recipients list, "Send me a preview now"; office hitting `/settings/notifications` directly gets a clean "No access" ErrorState (403), and the nav entry is gated on `org.manage` so office never sees it in the sidebar (screenshot 06) |
| 5 Account toggle | yes | `email-toggle-section.tsx` uses the same `me.notifications.get/set` query verified live above; wired into `account.tsx` |
| 6 Unsubscribe page | yes | Live GET/POST pass above matches the component's response handling (`postLink` → `{kind:"ok"}`/`{kind:"undone"}`/`{kind:"invalid"}`/`{kind:"rate_limited"}`/`{kind:"undo_refused"}`) exactly; **the page never calls `postLink` on mount** — only `onClick` handlers on the Unsubscribe/Undo buttons trigger a POST, so loading the page (or a link scanner following it) never unsubscribes anyone |
| 7 en/es, 390px, light/dark, 44px, no raw keys | yes | en/es catalogs are complete and parallel key-for-key (`src/i18n/en.ts`/`es.ts` diffs); screenshot 02 (es, 390px) shows no raw keys or English fallback; thumbs buttons are `size-11` (44px), reason chips `h-11`; all new components use the app's existing semantic Tailwind tokens (`bg-card`, `border-border`, `text-muted-foreground`, `bg-warning/10`, `text-danger`) with no hardcoded light-only colors, consistent with the rest of the dark-mode-capable app |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git -C invai-web diff --stat 5df9227..9b8a69e` lists exactly the card's owned globs: `src/lib/realtime.ts`, `src/routes/_app/digests/**`, `src/routes/_app/settings/notifications.tsx`, `src/routes/_app/account.tsx`, `src/routes/_app/index.tsx`, `src/routes/unsubscribe.tsx`, `src/components/digest/**`, `src/lib/nav.ts`, `src/i18n/{en,es}.ts`, plus generated `routeTree.gen.ts`; first commit `a800fbe` is the granted `alertKindLabel`/en/es addition for `ai_summary_breaker`)
- [x] Nothing outside scope — the one addition beyond the literal card text (`nav.ts`'s `digests` entry) is disclosed in the report and needed for AC2 (`/digests` must be reachable); it's a one-line, permission-gated nav entry, not a scope expansion of behavior
- [x] Tests exercise the behavior, and none were weakened — no unit tests were added for the new digest components (T-18-5's analogous `recommendation-copy.ts` has one; `digest-copy.ts` doesn't), but nothing was skipped, loosened or mocked either; the scan script's only hits are QA's own `test.fail` placeholders in a different commit
- [x] Tenancy / idempotency / money / en-es — this card has no server code (no `withTenant`/RLS to check); idempotency of the public link routes and `digest.recordClick`/`digest.feedback` was proven live (see Evidence); money is rendered only via the backend's own `formatted` cents strings, never recomputed client-side; en/es complete
- [x] Decisions recorded where needed — no new cross-cutting decision required from this card; the D8 `win.*` templateKey choice and the missing shared "retry in N seconds" helper are both disclosed in the report as open items for the tech lead, with safe fallbacks in place either way

## Optional notes (not blocking)
1. `src/components/digest/digest-copy.ts:141` (`sourceDateText`) formats the Market watch "week ending {{date}}" line with `new Date(asOf).toLocaleDateString(undefined, {...})`, which follows the browser's locale rather than the app's chosen language — the same latent bug as the pre-existing `src/lib/format.ts` `formatDay()`/line-25 helper (five other call sites already do this). The author disclosed the `formatDay` instance as a known gap but this is a second, new instance in code this card owns. Low severity (cosmetic, one line, no market item existed in my build to see it live); worth folding into whatever follow-up fixes `format.ts`.
2. D8 win `templateKey`: the author's `win.*` dot-key choice vs. T-19-3's observed "spec-table-text" convention (`"D6 action"` for D1–D7) is a real mismatch that the author flagged plainly in both the T-19-1 consumer review and this report, with a safe generic-celebration fallback so no raw key or blank UI can result either way. Tech lead should reconcile before the gate, but it isn't a defect in this card as built.
3. No colocated unit test for `digest-copy.ts`'s pure copy-building functions, unlike T-18-5's `recommendation-copy.test.ts` for the analogous market copy. Not required by the card's verification section; a coverage suggestion only.
4. Unsubscribe page and Referrer-Policy: the page loads no third-party resources (no external scripts, fonts or analytics — `index.html` has none globally either), so the signed token in the URL cannot reach a third party via the Referer header regardless of policy. An explicit `Referrer-Policy: no-referrer` would be a reasonable defense-in-depth addition, but it's a response header (backend/infra concern, outside this card's owned paths) — not a web-code gap and not blocking.
