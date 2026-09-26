# Waves 6+7 combined integration gate

- Run by: qa-engineer, 2026-09-26
- Result: **yellow. Two blocking bugs found and root-caused (not fixed — QA never fixes product
  code). Recommendation: do not push yet; both are small, precisely located fixes for their
  owners. See "Recommendation" at the bottom.**
- Evidence: logs in `/tmp/gate67-*.log` (temporary, this machine only) and
  `/tmp/etsy-listing-export.csv` / `/tmp/etsy-tracking-export.csv` (kept only as this report's
  evidence trail, not committed). Screenshots in `invai-docs/waves/7/gate/` (6, at budget).

## Why this gate used worktrees, not the shared tree
Wave 8 agents were actively committing directly to `main` in every JS/TS repo throughout this
gate (T-8-1, T-8-2, T-8-4 landed commits while this ran). `invai-contracts`, `invai-backend` and
`invai-web` were also dirty with in-progress edits at the moment this gate started. Per the
"Pinning contracts" rule, this gate created a clean, detached-HEAD worktree for **all seven**
repos next to their originals (`../gate67-<repo>`), each pinned to that repo's HEAD SHA at the
instant of creation, with a real (non-shared) `node_modules` per worktree whose `@invai/contracts`
(and `@invai/ui` for web/floor/ui) symlinks point at the sibling `gate67-*` worktrees — never at
the live, mutating shared repos. This fully isolates the gate from concurrent wave 8 activity;
every check below ran against the exact SHAs in the table, not against whatever `main` moved to
mid-run. All worktrees, their `node_modules` and the dedicated test DB were removed at the end;
nothing was left behind and nothing in a shared repo's own `node_modules` was touched.

**Note for future worktree-based gates:** `invai-web`'s and `invai-floor`'s E2E helpers hardcode
`../../../invai-backend/seed-output.json` (a sibling-repo-name path), so after seeding from a
`gate67-backend` worktree this gate also copied `seed-output.json` into the shared `invai-backend`
tree each time, or the E2E suites read stale/missing station tokens. Worth fixing in a future
`run-golden-path` revision (`E2E_BACKEND_DIR` env override) rather than every gate rediscovering
this.

## What was tested (pinned worktree HEADs, not the shared trees, not pushed)
All checks in §1–§3 and the smoke checks in §4 ran against these exact SHAs, captured the instant
each worktree was created:

| Repo | Tested HEAD | Notes |
|---|---|---|
| invai-contracts | `49f229a` | "AssistantEvent error code gains spend_cap (T-8-1, for B-15's spend breaker)" |
| invai-backend | `bb075e8` | "Etsy listing rules: AI disclosure wording, production_partner_ids, title rules (T-8-1, B-14)" |
| invai-ui | `c29c60a` | "A11y follow-up: Progress accessible name, Tabs' dangling aria-controls, success-color contrast (T-7-5 AC6)" |
| invai-web | `5c6ab28` | "Settings: production partner field for Etsy's production_partner_ids (T-8-1, B-14)" |
| invai-floor | `468d455` | "Fix demo Bin mock: id/name/archivedAt now that the contract Bin gained them (T-6-2)" |
| invai-imaging | `896163a` | "POST /labels/qr: request field is labels, matching T-6-1's blankLabels caller" |
| invai-infra | `148df7d` | up to date with origin |

**Wave 6 and wave 7 are both fully represented at these SHAs** (all 10 cards' commits are
ancestors), plus a few early wave-8 commits that had already landed on `main` before this gate
took its snapshot (see "Concurrent wave 8 activity" below) — this is a strict superset of waves
6+7, consistent with how wave 5's gate handled the same situation.

## Concurrent wave 8 activity (read before pushing)
Wave 8 agents (T-8-1 orders/listings/AI, T-8-2 assistant, T-8-4 trademark gate, plus review
worktrees) kept committing directly to every JS/TS repo's `main` throughout this gate — this is
expected under the team's "push directly to main, no branches" workflow, and this gate's own
worktree isolation (above) meant it was never affected by it. Two side effects worth flagging:

1. **A wave-8 commit already on this gate's tested `invai-backend` HEAD (`bb075e8`, T-8-1's B-14
   Etsy compliance work) has its own bug** — see bug #2 below. It blocks this gate's own golden-path
   step 11, but it is wave 8's regression, not wave 6/7's; flagging it here because this gate is
   what found it, not because wave 6/7 owns it.
2. **By the time this gate finished (not caused by this gate — this gate never pushed anything),
   `invai-backend` and `invai-web` were fully in sync with `origin/main`**, meaning something else
   pushed them during this run. `invai-contracts` (+11 ahead of origin), `invai-ui` (+2),
   `invai-floor` (+1) and `invai-imaging` (+3) were **not** in sync with origin as of this gate's
   end — still ahead, unpushed. This gate does not know who pushed backend/web or whether that was
   intended; flagging it for the tech lead rather than guessing, exactly as wave 5's gate did for
   wave 6's in-flight state.

## 1. Repo checks (all against the pinned worktree HEADs in the table above)
| Repo | typecheck | lint | test | build |
|---|---|---|---|---|
| invai-contracts | pass | pass (46 files) | **31/31** | n/a |
| invai-ui | pass | pass (54 files) | **24/24** | n/a |
| invai-imaging | ruff: pass ("All checks passed!") | n/a | pytest **30/30** | n/a |
| invai-backend | pass | pass (268 files) | **591/591** (see note) | pass (tsup) |
| invai-web | pass | pass (143 files) | **76/76** | pass (vite; chunk-size warning only, pre-existing) |
| invai-floor | pass | pass (73 files) | **86/86** | pass (vite + PWA; chunk-size warning only, pre-existing) |

**Backend test note:** first run showed 3 failed files / 7 failed tests (Shopify OAuth
state/webhook tests — `AssertionError`/timing-shaped failures) while several other agents'
`vitest`/`playwright` processes were simultaneously eating CPU on this machine (confirmed via
`ps aux` at the time). Reran the identical command with nothing else pending: **591/591 passed**,
same suite, same DB. Treated as proven environmental (CPU starvation, not a real failure) per
`run-golden-path`'s retry rule — not a product bug, not filed. All other suites ran clean on the
first try. Backend grew from 481 tests at wave 5 to 591 (waves 6+7's ten cards).

## 2. Database: reset, migrate, reference data, seed
- `db:reset` then `db:migrate` applied all migrations: **24** rows in
  `drizzle.__drizzle_migrations` (`0000`–`0023`; up from 19 at wave 5 — new: wave 6/7's
  `production_bin_name_archived`, `wave7_export_refunds`, `finance_refund_void`,
  `orders_channel_updated_at`, `ai_trademark_review`).
- `db:seed` ran **four** times during this gate (initial, before the browser E2E pass, before the
  floor suite, and a final closing reseed), each time with imaging up and the worker **stopped**
  first, per the seed rule. All four clean, EXIT 0: `{"orders":360,"items":~673,
  "transitions":~3880-3916,"dueSoon":88}`, ~25 sheets, ~585 transfers, 264 shipments, 108 inventory
  variants, ~149-151 listings.
- Final state left in the shared dev DB (closing reseed, run after all smoke checks and their
  side effects — the manual PO, bin, extra sheets, ad spend, refund, AI draft, labels and the
  `printsInHouse`/`productionPartner` settings this gate turned on — were all wiped by this last
  reset): 360 orders, 24 migrations, 151 listings. `seed-output.json` (copied into the shared
  `invai-backend` tree too, see the worktree note above) has the current logins/PINs/station token.

## 3. E2E suites
Health before each run: API `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`,
imaging `{"ok":true,"vips_version":"8.18.6"}`, web and floor both 200.

| Suite | Seed | Result |
|---|---|---|
| `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | fresh seed | **5 passed / 1 failed / 7 did not run** — step 6 ("send to vendor…") fails deterministically on `vendorPortal.inbox`'s output validation (bug #1 below); steps 7–13 never ran (sequential spec, sequential dependency on step 6's state). Not retried — root-caused as a real, always-reproducing bug, not environmental. |
| Reseed, 65 s pause, `pnpm e2e` (invai-web) | fresh seed | First pass caught this gate's own setup bug (stale `seed-output.json` in the shared tree — see worktree note), fixed, reran clean: **11 passed / 2 failed / 2 did not run**. `golden-path.spec.ts` steps 1–10 and `screens.smoke.spec.ts`'s owner-route pass (27+ routes, "No screen issues") passed; step 11 ("AI listing draft… passes Etsy rules") fails (bug #2); `screens.smoke.spec.ts`'s vendor-portal check fails (bug #1, same root cause as the API suite — the vendor portal page itself calls `vendorPortal.inbox`); steps 12–13 didn't run (sequential dependency on step 11). |
| Reseed, worker restarted, `pnpm e2e` (invai-floor) | fresh seed | **3/3 passed** (`floor.spec.ts`, `offline.spec.ts`, `press.spec.ts`), clean on the first try. |

### Bug #1 (blocking): vendor portal inbox always 500s — wave 6 regression
`invai-backend/src/modules/vendors/service.ts`'s `vendorInbox()` builds its per-status `counts`
object from a **hardcoded 9-element array** (`building, ready, sent, acknowledged, printed,
shipped, received, failed, cancelled`) — it's missing `"printing"`, the state T-6-2 added to
`SHEET_STATES` for the in-house print path. The contract's output schema
(`contract/vendors.ts:78`) is `counts: z.record(z.enum(SHEET_STATES), z.number()...)`, and zod v4's
`z.record` with an enum key **requires every enum value present** (verified directly: a 3-key
enum with one key's value omitted fails `safeParse`, confirmed against this repo's own installed
zod). So every call to `vendorPortal.inbox` — the vendor's own inbox list, and the owner-side
`/vendor` route the smoke tests hit — throws "Output validation failed" (500), deterministically,
regardless of data. Confirmed the blast radius is narrow: `vendorPortal.get` (deep-linking straight
to one sheet) is unaffected, which is why `golden-path.spec.ts`'s step 6 (which deep-links) passed
while the API suite's identical `vendorPortal.inbox({limit:100})` call and `screens.smoke`'s plain
`/vendor` visit both fail. Only one place in the codebase builds a `SheetState`-keyed object this
way (grepped `invai-contracts` for other `z.record(z.enum(SHEET_STATES)` — only this one). Exactly
the kind of miss wave 6's own clarifications caught once already (`badges.tsx`'s `SHEET_TONE`
record, which got a grant) — this one wasn't caught. **Filed for the vendors/service.ts owner: add
`"printing"` to the array (or better, derive the list from `SHEET_STATES` directly so it can't
drift again).**

### Bug #2 (blocking golden path, wave 8 in-flight, not wave 6/7): Etsy AI drafts can never pass
`invai-backend/src/modules/ai/service.ts`'s `productionPartner()` helper returns
`row?.settings?.productionPartner ?? null` — always a value, never `undefined`. But
`src/ai/validators/listing.ts`'s new check (from T-8-1/B-14, already on this gate's pinned
backend HEAD) is `if (channel === "etsy" && content.productionPartner !== undefined)`, and since
the helper always returns non-`undefined` (a name or `null`), this check **always runs** for
every Etsy draft — and the seed never sets a company's `settings.productionPartner`, so it always
fails with `production_partner_required`. Confirmed by setting a production partner through
`me.updateOrg` (an ordinary real-shop settings workflow, not a workaround) — generation
immediately passed ("Passes every channel rule") and the CSV export carried it through correctly
(see smoke check 4). This is wave 8's own in-flight work (B-14), not a wave 6/7 regression, but it
is what blocked this gate's golden-path step 11 and is worth flagging now rather than waiting for
wave 8's own gate. **Filed for the T-8-1/B-14 owner.**

Neither bug was retried — both are deterministic and root-caused to a specific line, not
environmental.

## 4. Wave 6+7 smoke checks (done for real in the browser/API, screenshots in `gate/`)

| Check | Result |
|---|---|
| **A manual PO marked placed, then received** | **Pass.** Created `PO-20260926-01` (S&S Activewear, Bella+Canvas 3001 · White · M × 24). "Mark placed by phone/email" → supplier order `SS-CONF-88213` → status **Submitted**. "Receive 24 units" → status **Received**, toast "Received into stock". Screenshot `gate/1-po-placed-then-received.jpg`. |
| **The in-house print path on a sheet, and a bin label PDF** | **Pass.** Turned on `printsInHouse` (no settings UI yet — known wave 6/7 follow-up, set via API), built fresh sheets; a 90%-film-use sheet showed **Print in-house** → **Printing** → **Mark printed** → **Printed**, skipping the vendor entirely (no Sent/Acknowledged step, confirmed in the Details panel). Screenshot `gate/2-inhouse-print-sheet-printed.jpg`. Created bin `BIN-QA1`, called `production.bins.labels` → a real S3-backed PDF key; downloaded and rendered it — one page, a real QR code encoding `BIN:BIN-QA1` under "QA Gate Bin". Screenshot `gate/3-bin-label-qr-pdf.png`. |
| **Add ad spend and see profit change** | **Pass.** Added $500 Etsy ad spend ("QA Gate campaign") via Settings → Ad spend; running total went `$2,528.51 → $3,028.51`. Analytics → Profit's Last-30-days totals changed accordingly on reload. Screenshot `gate/4-ad-spend-profit-change.jpg`. |
| **Export an Etsy listing CSV with real SKUs** | **Pass.** Set a production partner (needed to clear bug #2), generated + approved an Etsy AI draft for design `DB040 · Lake Powell Weekend` (36 variants), exported via `ai.exportCsv` → a 36-row CSV, one row per **variant** (not per draft), each with a real blank SKU (`G64000-WHT-S` … `G64000-NVY-XL`, all 36 unique), `production_partner`/`production_partner_ids` populated, bilingual AI-disclosure text present. File kept as `/tmp/etsy-listing-export.csv` (evidence, not committed); no screenshot spent here — the file's real SKUs are the stronger evidence. |
| **A demo workspace buys a label with the mock only** | **Pass.** Switched into "Sample shop" (Try with sample data — a separate company id from Desert Bloom Tees). Bought a label on order `#113-2025508-1000364` through the normal Rates → Buy & print flow; mock rates (USPS/UPS, round dollar figures), label bought with tracking `9400407371693074353224`. `EASYPOST_API_KEY` is empty in `.env` (confirmed) — no real carrier account was ever contactable, so this necessarily used the mock. Left the demo afterward. No screenshot spent here (already at the 6-screenshot budget; the label-bought toast and tracking number are the evidence). Separately confirmed every seeded company (including Desert Bloom Tees itself) carries `demo: true` by design (B-109's spend-can't-happen safety net, wave 6 T-6-5), so in fact *every* label bought anywhere in this gate — including check 8 below — was demo-safe. |
| **Export Etsy tracking** | **Pass.** `shipping.exportTracking({channel:"etsy", since:null})` → a 106-row CSV in Etsy's exact bulk-tracking-upload column format (`receipt_id,tracking_code,carrier_name,note_to_buyer,send_bcc`), one real Etsy receipt id and USPS tracking number per shipped Etsy order. File kept as `/tmp/etsy-tracking-export.csv`; no screenshot (a CSV's correctness isn't a picture, and the budget went to the checks that are actually more legible as screenshots). |
| **Record a manual refund, and see it in profit** | **Pass.** On order `#113-2000000-1000000`'s detail page (Profit panel → refund form), recorded a $15.00 refund. Toast "Refund recorded"; the order's own **Net profit dropped from $39.96 to $27.00 immediately** (Refunds −$15.00, referral fee recovered −$2.04 shown separately). Screenshot `gate/5-manual-refund-profit-change.jpg`. Note: the company-wide "Last 30 days" analytics/profit summary cards did *not* show this refund even after Recompute — investigated and this is **not a bug**: the refund date picker defaulted the timestamp to later the same day (Phoenix-local business hours) than the actual current wall-clock moment, and a live "as of right now" 30-day window correctly excludes a refund dated in its own future. Confirmed directly against the `finance.profit` API (both `dimension: "day"` and `dimension: "design"`) that the row for 2026-09-26 and the response's own `totals` both already include the $15 (1500 cents) the instant its timestamp is in the past — i.e., the date-based bucketing (T-7-2's whole point) is working correctly. |
| **The label fee is 10¢ on a paid plan** | **Pass.** Desert Bloom Tees is on the "growth" (paid) plan. Bought a label on order `#3104008806` → `shipments.label_fee_cents = 10` in the DB, and the order detail's Shipment card reads "Cost: $11.60 postage + **$0.10 label fee**". Screenshot `gate/6-label-fee-10-cents.jpg`. |

## Failures
Two blocking bugs (§3, both root-caused to one exact line each, filed to their owners, neither
fixed by this gate). No flaky retries beyond the one proven-environmental backend unit-test rerun
(§1). All eight wave 6+7 smoke checks pass with evidence.

## Cleanup
- Worktrees: all seven `gate67-*` worktrees (and their standalone `node_modules`, `.venv` symlink)
  removed (`git worktree remove --force` from each origin repo, then `git worktree prune`);
  `git worktree list` in every repo now shows only the repo's own primary worktree.
- App processes this gate started (imaging on :8000, api and worker via `tsx watch` on :3000,
  web on :5173, floor on :5174 — all from the `gate67-*` worktrees) were all stopped by their
  recorded PIDs. Confirmed after: `lsof -iTCP:3000 -iTCP:8000 -iTCP:5173 -iTCP:5174` empty.
  **Not touched, not mine:** port 3175/3192-3194-range processes from wave 8 agents' own dev
  instances — never killed, per `agent-brief.md`.
- Dedicated gate test DB `invai_test_gate67` dropped (`invai_test` untouched).
- Infra (Docker) left running: 4/4 local containers healthy.
- The dev DB is left freshly reset (24 migrations) and seeded (360 orders, 151 listings) — this
  gate's own smoke-check mutations (the manual PO, extra sheets, bin, AI draft, ad spend, refund,
  labels, and the `printsInHouse`/`productionPartner` company settings) do not persist; the
  closing reseed in §2 wiped them all. `seed-output.json` is current in `invai-backend`.
- `df -h /`: **8.1 Gi available** (228 Gi total, 60% used) — above the 5 GB floor (worktrees and
  git's extra object storage used several GB during this gate; all freed on worktree removal).
- Nothing was pushed. This gate's own output (`invai-docs/waves/7/gate.md` and
  `invai-docs/waves/7/gate/`) is committed here with a pathspec.

## Recommendation
**Do not push yet.** Every repo's typecheck/lint/test/build is green against the pinned wave 6+7
HEADs (contracts 31/31, ui 24/24, imaging ruff+30/30 pytest, backend 591/591, web 76/76, floor
86/86, all builds clean), the DB reset/migrate/seed cycle is clean and reaches migration 24, the
floor suite is 3/3, and all eight wave 6+7 smoke checks pass with evidence (PO placed→received,
in-house print + bin label, ad spend affecting profit, a real-SKU Etsy CSV export, a demo-only
label purchase, an Etsy tracking export, a refund correctly bucketed by its own date, and the
10¢ paid-plan label fee).

But the API and browser golden paths are **not** fully green: bug #1 (vendor portal inbox
always 500s — a wave 6 regression, one exact line, `modules/vendors/service.ts`'s hardcoded
`SheetState` list missing `"printing"`) and bug #2 (Etsy AI listing drafts can never generate
without a production partner set — wave 8's own in-flight B-14 work, also one exact line) both
block steps of the standard 13-step suite. Neither is fixed here — QA proves and files, owners
fix — but both are small and precisely located. Recommend: the vendors/service.ts owner takes
bug #1 (it's the more clearly wave-6/7-owned of the two and blocks a real user-facing page, not
just this gate's own suite), wave 8's B-14 owner takes bug #2, then a short re-run of just the
two affected suite steps (no full re-gate needed) before push.

Also read "Concurrent wave 8 activity" above before deciding on the push itself: as of this
gate's end, `invai-backend` and `invai-web` were already in sync with `origin/main` (pushed by
something other than this gate, mid-run), while `invai-contracts`, `invai-ui`, `invai-floor` and
`invai-imaging` were still ahead of origin, unpushed. This gate didn't push anything and doesn't
know who did or whether it was intended — flagging it for the tech lead rather than guessing,
same as wave 5's gate did for wave 6's in-flight state.
