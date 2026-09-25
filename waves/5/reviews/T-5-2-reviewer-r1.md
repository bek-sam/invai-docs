# Review of T-5-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web log --oneline origin/main..HEAD` (context) | `a2566b2` is the reviewed commit; `bca872f` (T-5-1) sits on top of it, not reviewed here |
| `git worktree add ../invai-web-t52-review a2566b2` | clean checkout at the exact commit |
| `node_modules/.bin/tsc --noEmit` (worktree) | no errors |
| `node_modules/.bin/biome check .` (worktree) | `Checked 124 files … No fixes applied.` |
| `node_modules/.bin/vitest run` (worktree) | 11 files, 66 tests passed |
| `node_modules/.bin/vite build` (worktree) | `✓ built in 1.19s` (only the pre-existing >500kB chunk warning, unrelated) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web-t52-review a2566b2^` | `Result: no hits` (0 removed / 28 added assertions, no skips/mocks/snapshot changes) |
| i18n key-parity check (`node --experimental-strip-types`, flattened `en.ts`/`es.ts`) | 1381 keys each side, 0 missing either way; the 32 identical en/es values checked are abbreviations/units (`API`, `sandbox`, `Error`, `PDF, 4×6 in`), not untranslated prose |
| `grep -nE 'aria-label="[A-Za-z]\|placeholder="[A-Za-z]\|title="[A-Za-z]'` on the changed files | only two literal placeholders, both format examples (`your-shop`, `G185`), not prose |
| `grep -nE '>[A-Z][a-zA-Z]+( [a-zA-Z]+){1,6}<'` minus `{t(` on the changed files | no hits — no raw English JSX text |
| Backend: `pnpm db:migrate` against a fresh copy `invai_t52_review` (from `invai` via `createdb -T`) | `[migrate] up to date` |
| Live stack: API `PORT=3192` + worker, `DATABASE_URL`→`invai_t52_review`, `REDIS_URL=redis://localhost:6379/10`, backend at HEAD (`72c1139`); web `vite --port 5192 --strictPort`, `VITE_API_URL=http://localhost:3192` | started clean, mocks on (`ai,carrier,shopify,supplier,billing,mail`) |
| Browser pass (owner login) | see "Acceptance criteria" below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. OAuth return states | Yes | Live: `?connected=shopify&connectionId=<bogus>` → translated success banner, falls back gracefully when the id doesn't resolve; dismiss (`×`) clears the banner **and** the query params. `?error=expired` → translated "The Shopify approval link expired… Connect the store again." banner with "Connect again". `status.ts`'s `readOAuthReturn` only uses the raw server `error` text for regex classification; `channels.tsx` never renders `.detail`, so the server string never reaches the screen — confirmed by grep. |
| 2. Import history, health, Reconnect, stock toggle | Yes | Live: uploaded `invai-backend/src/integrations/channels/csv/fixtures/etsy-sold-order-items.csv` to the Etsy connection → "6 rows · 4 new · 0 updated · 1 failed", badge "Done, some rows failed", row expands to `#7 Missing quantity`. Stock-push switch on the Shopify card toggled on with a toast + Undo, hidden on the CSV/pending connections as required. Health/Reconnect matches `channels-issues-en.png` (token-lost issue with collapsible Details, pending install with a working Reconnect button). |
| 3. Shipping settings | Yes | Live at `/settings/shipping`: allowed carriers (USPS/UPS checkboxes), label format ("PDF, 4×6 in", ZPL shown with a "coming soon" hint), package presets with translated field labels (`Length (in)`, `Width (in)`, `Height (in)`, `Empty weight (oz)`, `Up to (items)`, `Use when nothing else fits`) — no hard-coded "L (in)"/"Poly mailer" field labels anywhere; "Add preset" inserts a preset whose name is the translated default. Ship-from address and Test-mode badge render as in `shipsettings-es-dark.png`. |
| 4. Void confirm, T-2-5 rules | Yes | Code: `shipping/service.ts:1145-1244` blocks void unless `status === "labeled"` (a carrier scan moves a shipment to `in_transit` per `jobs.ts`'s `applyReading`/`markInTransit`, independent of any tracking push — this is what keeps CSV orders, which are in `NO_PUSH_CHANNELS`, voidable "right up to the scan"), blocks when `trackingPushStatus === "pushed"`, and blocks when any order item is `shipped`/`delivered`. `shipping.tsx`'s `VoidLabelDialog` states, verbatim, all three T-2-5 points (refund may show pending, only-unscanned + CSV-stays-voidable, blocked-once-pushed), maps `VOID_REJECTED`/`UPSTREAM_FAILED`/`CONFLICT` to plain text, and for an already-pushed shipment shows the red banner with only "Got it" (`onConfirm` no-ops when `pushed`). Visually confirmed against `void-pushed-en.png`, which matches this exactly. I could not reproduce a fresh successful void live myself (imaging wasn't running, so `Buy & print` couldn't confirm a label with the mock carrier, and my own attempt to hand-edit a shipment into `labeled` in the DB copy briefly broke `shipments.list`'s output validation on an unrelated field — reverted, not a code defect, see notes). The report's own DB check (shipment → `voided`, label → `voided`) plus the matching screenshot are sufficient evidence together with the code read. |
| 5. en/es, 390 px, keyboard | Yes, with the same disclosed gap as the report | 1381/1381 i18n keys, no raw English. All icon-only buttons carry translated `aria-label`s (`X`, `Settings2`, `Unplug`, `Trash2` in the diffs). The stock-push `Switch` is wired `id` + `<label htmlFor>` + `aria-describedby` to its hint text. The weight-per-style row uses `grid-cols-[minmax(0,1fr)_6rem_auto]` with `min-w-0` on the Field, which is the fix for the 390 px overflow the report mentions. No dedicated keyboard-only walkthrough was done (author's disclosed gap, token budget) — not blocking, since every control is a native `button`/`input`/`select`/`details` and the shared `ConfirmDialog`/`Switch` are Radix primitives already relied on elsewhere in the app. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — see "Optional notes" for the two exceptions the tech lead asked to be judged.
- [x] Nothing outside scope — every file serves AC 1-5; the exceptions below are infrastructure for the owned change, not new scope.
- [x] Tests exercise the behavior, and none were weakened (scan: no hits; 0 removed / 28 added assertions; `status.test.ts` asserts real classifications, not shape-only)
- [x] Tenancy, idempotency, money in cents, en/es text — no backend files are in this diff (`git diff --stat` is 100% `invai-web`), so tenancy/RLS/idempotency are unchanged and out of scope for this card; en/es verified above.
- [x] Decisions recorded where needed — none needed; this implements existing decisions (`0003` stock-push opt-in) and an existing rule set (T-2-5), it doesn't create new ones.

## Optional notes (not blocking)
1. **`src/lib/nav.ts` (+8 lines) and `src/routeTree.gen.ts` (+21 lines) are outside the card's listed owned paths.** Judgment: `routeTree.gen.ts` is Vite/TanStack Router's generated output for the new (owned) `routes/_app/settings/shipping.tsx` file — mechanical and unavoidable, in the same spirit as the i18n catalogs the ownership rules already tolerate. `nav.ts` is hand-written and genuinely not on the card's owned-paths list, so strictly it needed a grant that wasn't asked for. I'm not blocking on it: it's a pure 8-line addition (no edits to any other nav entry), it doesn't collide with T-5-1's concurrent diff (confirmed `bca872f` never touches `nav.ts`), it's required for the new page to be reachable from Settings at all, it's correctly gated behind `shipping.manage`, and the author flagged it themselves in the report rather than hiding it. Recommend the tech lead either add a retroactive grant note or fold "one nav entry for a card's own new top-level page" into the shared-file carve-outs in `operating-system.md`, so future cards don't need to guess.
2. Consider a short keyboard-only pass (Tab/Shift+Tab through the void dialog and the stock-push switch) before the wave gate, given the reused primitives make this low-risk but it's still an unverified claim.
3. Pre-existing, not introduced here: `@invai/ui`'s `RelativeTime` renders English ("6 hours ago") inside Spanish screens — already logged by the author as a follow-up owned by `product-designer`.
