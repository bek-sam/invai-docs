# Review of T-19-5 (round 1)

- Reviewer: product-designer on sonnet
- Author: web-engineer on sonnet
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| Read card `T-19-5.md`, spec `specs/weekly-digest.md` (Copy table, Screens and flow, AC1-AC33), my spec review `spec-weekly-digest-product-designer.md` | restated AC1-7 as observable results before reading code |
| `git -C invai-web show 9b8a69e --stat` | matches the card's owned globs (`src/lib/realtime.ts`, `src/routes/_app/digests/**`, `settings/notifications.tsx`, `account.tsx`, `index.tsx`, `unsubscribe.tsx`, `src/components/digest/**`, `src/i18n/{en,es}.ts`, `src/lib/nav.ts`, generated `routeTree.gen.ts`); commit `a800fbe` is the granted `ai_summary_breaker` unblock |
| Read `invai-contracts/src/schemas/digest.ts` (`DigestInsight.templateKey: z.string()`, `DigestActionParams.costLine: z.string()`) | `templateKey`/`costLine` are free strings, not enums shared with the backend |
| Read `invai-backend/src/modules/digest/detectors.ts` (D3, D8 candidates) and `render.ts` (email `TEMPLATES`) | confirmed the **actual** wire values these fields carry (below) |
| Read `invai-web/src/components/digest/digest-copy.ts`, `insight-card.tsx` | confirmed how the web renders `templateKey` and `costLine` |
| Read `src/i18n/en.ts`/`es.ts` diff against the spec Copy table | D1-D7 actions, feedback reasons, shadow-mode toggle, unsub done/undo, footer all match the spec's approved wording verbatim, en and es |
| Read `src/routes/_app/digests/$weekKey.tsx` | pending / NOT_FOUND (`notReady`) / other error / steady / `skipped_quiet` / incomplete / one `partial` row per channel / opt-in / glance / planUsage / actions / win / marketWatch / ask — all present |
| Read `src/components/digest/feedback-thumbs.tsx` | `aria-label` on both thumbs (`upAria`/`downAria` include the action text), `aria-pressed`, `size-11`/`h-11` (44 px) targets, reason chips show real i18n text |
| Read `T-19-5-reviewer-r1.md`, `T-19-1-web-engineer-r1.md` | both flagged the D8 `templateKey` mismatch as an *optional*, disclosed, "graceful fallback" gap, not exercised against a real win (this week's build had `win: null`) |

I did not re-run the app; the two findings below are verified by reading the shipped code paths on both sides of the wire, not by observation, and don't depend on a live build.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Today card | yes | `today-card.tsx` on `digest.latest`/`me.notifications`, wired to `digest.ready` in `realtime.ts` |
| 2 Digest page | **no** | glance/actions/market/thumbs/states all present, but "the win" section (`DigestWinCard`) never renders correct copy — see Blocking #1 |
| 3 First-digest opt-in | yes | `optIn.prompt`/`optIn.button` on `me.notifications.set`, shown when not opted in |
| 4 Settings -> Notifications | yes | day/hour/tz, `settings.aiSummaryShadow` disabled copy, recipients, preview; office `FORBIDDEN` |
| 5 Account toggle | yes | `email-toggle-section.tsx`, same `me.notifications` calls |
| 6 Unsubscribe page | yes | confirm/done+Undo/undone/undo-expired/rate-limited/invalid states against `/l/:token` |
| 7 en/es, 390px, 44px, no raw keys | **no** | D3's `review_costs` action shows the internal enum value (`channelFees`, `blankCost`, ...) verbatim in both languages instead of the plain word — see Blocking #2 |

## Blocking findings

1. **`src/components/digest/insight-card.tsx:1` → `DigestWinCard` / `digest-copy.ts:digestWinText`** — the win headline can never show the real win. `detectors.ts` (`d8Wins`, lines ~318-354) sends every D8 candidate with `templateKey: "D8 win"` (one literal string for both the best-net-week and on-time-record cases; they're told apart only by `facts`, e.g. `d8.net`/`d8.weeks` vs `d8.onTimeRate`, which the wire schema (`DigestInsight.facts`) carries but this card never reads). `digestWinText`'s switch only matches `"win.best_net_week"`, `"win.on_time_record"`, `"win.design_milestone"` — strings the author invented and that never appear on the wire. Every real win therefore falls to the generic fallback: *"Something worth celebrating this week."*, with no number, no week count, no rate — even though `impactCents` and `facts` are sitting right there on `insight`. Failure scenario: Desert Bloom Tees has its best net week in 8 weeks (D8 `bestNet` fires, `impactCents` set); the owner opens the digest expecting "Your best net week in 8 weeks: $1,240" (the backend's own `render.ts` copy for the exact same fact) and instead sees a vague, unquantified line — the one section of the page whose entire job is to name a number. This isn't a hypothetical mismatch the tech lead can leave as a "same-day follow-up": as shipped, the win card is dead code for its real purpose. Fails AC2 ("the win") and card AC2.
   - Fix: read `insight.facts` (or a `kind` on the action/insight) to pick the right headline and substitute the number, and align the key vocabulary with `detectors.ts`/`render.ts` (`"D8 win"` plus a fact-based branch, not a second, uncoordinated key set) so web and the email renderer say the same thing for the same fact.

2. **`src/components/digest/digest-copy.ts:review_costs` case** — `costLine: params.costLine ?? ""` interpolates the raw `CostLine` enum value (`"channelFees"`, `"blankCost"`, `"transferCost"`, `"labelCost"`, `"packagingCost"`, `"laborCost"`, `"adsCost"`, `"refunds"` — confirmed in `invai-backend/src/modules/digest/detectors.ts:12-20`) straight into `"Review {{costLine}} costs"`. There is no `digest.costLine.*` lookup in `en.ts`/`es.ts` (confirmed absent) even though the backend's own email renderer already has one (`render.ts`: `"costLine.channelFees": "channel fee"` / `"comisiones del canal"`, etc.) with real words in both languages. Failure scenario: a shop's margin slips because of ad spend; D3 fires; the button reads **"Review channelFees costs"** in English and, unchanged, in Spanish too — a raw camelCase internal identifier shown to a shop owner, not plain language, and with zero Spanish translation despite AC7's "en/es ... no raw keys" and principle #4 ("plain shop words"). This is directly parallel to the D8 finding: a backend enum crossing the wire untranslated because the web card built its own copy layer instead of consulting (or asking for) the same lookup table the backend already has.
   - Fix: add the 8 `digest.costLine.*` keys (en/es) mirroring `render.ts`'s `costLine.*` text, and look up `params.costLine` through it before interpolating.

## Checks
- [x] Only owned paths changed (`git diff --stat` matches the card's globs)
- [x] Nothing outside scope (the one-line `nav.ts` `digests` entry is disclosed and needed for AC2's `/digests` reachability, not scope creep)
- [x] Tests exercise the behavior, none weakened — no unit test exists for `digest-copy.ts`'s pure functions (T-18-5 has one for the analogous `recommendation-copy.ts`); a test covering `digestWinText`/`review_costs` against real backend values would have caught both findings above before this review
- [x] Tenancy/idempotency/money — n/a to this card (no server code); en/es otherwise complete and verbatim to the spec Copy table except the two findings above
- [x] Decisions recorded where needed — the D8 mismatch is disclosed in the report and both prior reviews as a "same-day follow-up"; this review treats it (and the newly-found costLine gap) as blocking rather than a follow-up, since both are now verifiably wrong copy in shipped code, not a coordination risk that might land wrong

## Optional notes (not blocking)
1. `formatDay()` (`src/lib/format.ts`, not owned by this card) uses `toLocaleDateString(undefined, ...)`, the browser's locale rather than `i18n.language`. It **is** visible in this digest: the page title (`digest.page.title`, "Week of {{day}}") and `/digests` list rows (`digest.list.weekOf`) render the weekday/month in the browser's locale even when the app language is Spanish (confirmed live by the author's own Spanish screenshot showing "Mon, Sep 21"). Pre-existing, used the same way elsewhere in the app, and correctly flagged by the author as a `format.ts` fix, not this card's — not blocking here, but worth the tech lead confirming it's tracked once, not per-card.
2. Reuse `band.high`/`band.medium` and the market vote copy is confirmed unmodified from T-18-5 (`RecommendationCard`/`SampleDataBadge` imported, zero diff under `src/components/market/**`), matching my spec-review note.
3. `sourceDateText()` has the same browser-locale date issue as #1, one level down (Market watch's "week ending {{date}}" line); same disposition.
4. Glossary/plain-language spot check: `digest.steady`, `digest.skippedQuiet.*`, `digest.paused`, footer/unsub copy all read naturally in Spanish and match the spec table; no new shop vocabulary needs a glossary addition beyond what the spec review already logged.
