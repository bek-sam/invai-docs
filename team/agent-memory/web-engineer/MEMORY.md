# web-engineer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- 2026-09-24 v1: Check the installed library API in `node_modules` before writing code (oRPC 1.15, drizzle 0.45, Zod 4, TS 7, Better Auth 1.7 are newer than training data).

## Learned on cards
- [Dev CSP needs build+preview](feedback_dev_csp_needs_build_preview.md) — `pnpm dev` CSP is hard-coded to :3000; use `vite build`+`preview` with `VITE_API_URL` and set `WEB_ORIGIN` on the API for a custom-port browser pass.
- [Never pkill](feedback_never_pkill.md) — always `lsof` for the PID then `kill <pid>`; never `pkill`/`killall`, even with a specific-looking filter.
- [T-17-4 assistant starters](project_t17_4_assistant_starters.md) — wave 17 tool-chip/starter-question pattern for the assistant screen; follow it for future analyst tools.
- [T-18-5 market signals](project_t18_5_market_signals.md) — 3 pre-existing e2e/harness gaps found and routed (not fixed by editing QA's tests): oRPC assistant-stream abort, sidebar/starter text collision, es-before-login helper bug.
- [Flatten chip text for e2e](feedback_flatten_chip_text_for_e2e.md) — a spec's one-sentence copy (label + comma list) must be one text node; adjacent sibling elements don't get a space/comma from CSS gap in `textContent`.
- [T-19-5 digest web](project_t19_5_digest_web.md) — new routes need one `vite build` to regen `routeTree.gen.ts` before typecheck; `AnyLink` has no `params`, split combined `href` strings yourself; `formatDay`/`formatDate` use browser locale not app language (pre-existing bug); a free-string contract field (no enum, no spec copy) needs your own keys + generic fallback, flagged for reconciliation, not a blocker.
- [StatCard has no neutral/no-arrow state](feedback_statcard_no_neutral_direction.md) — it always draws an arrow when `delta` is set; build a local tile on `Card` instead, report the gap to product-designer.
- [T-20-2 billing.tsx locale gap](project_t20_2_billing_locale_gap.md) — billing.tsx's numbers ignore app language (`.toLocaleString()` no locale); out of T-20-2's owned paths, so QA's AC4 Spanish e2e case stays red there. Round 2: digest's `localeNumber()` is now `es-US` (not bare `es`), per PM decision.
- [Mirror backend copy fallbacks](feedback_mirror_backend_copy_fallbacks.md) — T-20-2 r1: an optional field's empty-case fallback in web copy must match the backend's fallback for the same record, not just avoid crashing/raw keys.
- [T-21-5 help/legal pages](project_t21_5_help_legal_pages.md) — claude-in-chrome's browser picker blocks a subagent with no way to answer; use `@playwright/test`'s bundled Chromium instead. Also: frontmatter `title` duplicates the body's first `# Heading`, drop `blocks[0]` before rendering.
- [T-23-1 P2 sweep](project_t23_1_p2_sweep.md) — r1: Alert.data isn't on the wire; i18n-es.json/en.ts 384-key drift; dynamic-key catalogs need i18n-extra-en.json; `<li className="flex">` drops bullets. r2: i18n-es.json can drift from hand-edited es.ts (diff before regen); flatten generated i18n .ts via `await import()`, Node 24 strips TS types for free; `tr(...)` alias/template keys evade the extractor; `vite preview`'s prodCsp blocks local http MinIO images (not a bug).
- [Vite manualChunks before blaming tree-shaking](feedback_vite_manualchunks.md) — a Rollup chunk's filename names one module inside it, not necessarily the bulk; grep the built file before assuming a lucide-react/tree-shaking bug.
- 2026-09-29 T-24-1 r1 (co-review): new csp.ts branches (uploadOrigin/connectSrc 2nd arg) shipped with no unit test — grant named only csp.ts, not csp.test.ts; treated as non-blocking fast-follow since live-exercised correctly, not a scope gap for the author.
- [T-A6 Profit v2](project_t_a6_profit_v2.md) — `analytics.*` `*Pct` fields are percent-numbers (×100), not ratios, despite a misleading schema comment; matters for T-A7 too.
- [Locale currency NBSP overflow](feedback_locale_currency_nbsp_overflow.md) — Spanish `Money` strings join with a non-breaking space; fix cell width, `break-words` alone just moves the clip to an uglier spot.
- [Tabs needs an overflow wrapper](feedback_tabs_needs_overflow_wrapper.md) — `TabsList` has no overflow handling; wrap in `-mx-1 overflow-x-auto px-1` whenever it might not fit at 390px.
- [T-A7 Ops/Inventory/Today](project_t_a7_ops_inventory_today.md) — i18n dynamic-key gotchas (gen-i18n.py leaf/prefix crash, extractor blind to `t(var, default)`), app lang key is `invai.lang` not `i18nextLng`, theme is `invai.theme`, PageHeader actions clip (not scroll) past ~3 controls at 390px (pre-existing, reported not fixed).
- [oRPC .queryOptions() always aborts on unmount](feedback_orpc_queryoptions_always_aborts.md) — use `.call()`+`.queryKey()` directly to let an in-flight read finish quietly instead of surfacing as aborted.
- [T-P2-1 lazy thumbnails](project_t_p2_1_lazy_thumbnails.md) — invai-ui `Skeleton` has no `data-slot=skeleton` today (settled() doesn't actually wait on it); restart the API to clear the in-memory sign-in rate limiter before re-running e2e manually.
- [Login resets locale from session](feedback_login_resets_locale_from_session.md) — pre-login `localStorage["invai.lang"]` gets overwritten by `routes/login.tsx` from `user.locale`; use the account-menu toggle after sign-in instead, and reset the account's locale back to `en` after.
- [Never run pnpm i18n](feedback_never_run_pnpm_i18n.md) — agent-brief overrides the skill: hand-edit `en.ts`/`es.ts`/`i18n-es.json` for new keys, don't regenerate mid-wave.
- [T-P4-3 Spanish sweep](project_t_p4_3_spanish_sweep.md) — bug class: English literal wrapped around an already-localized number (e.g. `"{{n}} in / {{n}} out"`); Playwright `fullPage` screenshots need `document.querySelector("main").scrollTo(0, 999999)` first, the real scroller isn't `document.body`.
- [designs.index "new" link matches card selector](feedback_designs_new_link_matches_card_selector.md) — `a[href*='/catalog/designs/']` hits the "New design" button before any card; exclude `:not([href$='/new'])`.
- [Intl date trailing punctuation](feedback_intl_date_trailing_punctuation.md) — a template ending `{{date}}.` double-punctuates in es-MX ("4:30 a.m.."); drop the trailing period when an Intl-formatted value is the last token.
- [T-P5-5 reason codes](project_t_p5_5_reason_codes.md) — route-file pure helpers: colocated test as `-index.test.ts` (router-plugin ignore prefix); `?view=blocked`/`needs_mapping` finds seeded orders with a real reasonCode to screenshot.
- [T-P7-3 confidence badge](project_t_p7_3_confidence_badge.md) — `initI18n` from `@invai/ui` loads the kit's en/es JSON into the same `translation` namespace web layers onto; diff before dropping web's old keys vs. passing `label`.
- [Server-cap copy no owner agency](feedback_server_cap_copy_no_owner_agency.md) — a server-controlled cap's error copy must not say "ask the owner" or claim it's the shop's own limit.
