# Waves 6–9 integration gate (plus T-12-1, T-12-2, T-13-5 part 1)

- Run by: qa-engineer, 2026-09-26
- Result: **yellow. Two blocking bugs found and root-caused (not fixed — QA never fixes
  product code). Recommendation: do not push yet.** Everything else — all six repos'
  typecheck/lint/test/build, the DB reset/migrate/seed cycle, the full API + browser +
  floor golden-path suites, and five of the seven required smoke checks — is green.

## What was tested (pinned worktrees, not the shared trees, not pushed)
Per the agent brief's "Pinning contracts" rule, T-12-3 and T-13-5 have uncommitted work in
`invai-backend`, and other agents were actively committing to every repo's `main` throughout
this run, so this gate created a clean, detached-HEAD worktree for all six JS/TS/Python repos
next to their originals, each pinned to the exact SHA below at creation, with its own
non-shared `node_modules` (contracts/ui `.pnpm` store cloned via APFS `cp -c`, top-level
symlinks copied as-is) and its own `.venv` symlink (imaging). The worktrees were nested one
level deeper than usual (`invai/gate9/<repo>/`, not `invai/gate9-<repo>`) specifically so each
repo's own `link:../invai-contracts` / `link:../invai-ui` protocol resolves to the sibling
pinned worktree by construction — no manual re-linking needed, and pnpm's own script-launch
self-heal (which silently relinks a manually-pointed symlink back to whatever `link:` says)
can't undo it.

| Repo | Tested HEAD | Commit |
|---|---|---|
| invai-backend | `aa13ec0` | NUL-safe text at the oRPC input boundary and the order-import pipeline (T-8-6, OI-5) |
| invai-contracts | `02518b8` | Format sheetSpecPdfCapError signature (biome; T-9-3 lint fix) |
| invai-web | `fbe4507` | Alert labels for queue_failed_spike, outbox_parked, ai_breaker_fail_open, en and es (T-12-1) |
| invai-floor | `468d455` | Fix demo Bin mock: id/name/archivedAt now that the contract Bin gained them (T-6-2) |
| invai-ui | `c29c60a` | A11y follow-up: Progress accessible name, Tabs' dangling aria-controls, success-color contrast (T-7-5 AC6) |
| invai-imaging | `c872d19` | ruff format app/labels.py (granted, was failing ruff format at HEAD) |

Waves 6–9 are fully represented at these SHAs (all cards through wave 9, plus wave 8's B-14
Etsy compliance work — both wave-7-gate bugs are confirmed fixed here, see §3), plus T-12-1
(retries/DLQ/sweeps, on `invai-web`'s pinned SHA) and T-12-2 (`/livez`/`/readyz`, confirmed
live in §4). T-12-3, T-12-4, T-12-5 and T-13-5's own uncommitted work are **not** represented
(per instructions, committed HEAD only) — T-13-5 **part 1** (seed efficiency) is, since the
seed now finishes in ~25s instead of wave 7's 15–20 min, confirmed below.

## Mid-gate incident: workspace moved
Partway through (after repo checks, DB seed and the API golden path had already passed), the
owner relocated the workspace from `~/Desktop/projects/invai` to `~/invai`. The move carried
the `gate9/` worktrees along as siblings, but broke `git worktree` metadata (the main repos'
`.git/worktrees/<name>/` admin directories were missing after the move — `git worktree repair`
alone couldn't recreate them from nothing) and one symlink baked with an absolute old-path
target (`gate9/invai-imaging/.venv`), plus every Python venv script's shebang line still
pointing at the old absolute path. Fixed in place: hand-wrote each worktree's `.git` file and
its main repo's `.git/worktrees/<name>/{HEAD,commondir,gitdir}`, then `git reset --mixed HEAD`
to rebuild each worktree's index (git status confirmed clean afterward, all six at their pinned
SHA); re-pointed the imaging `.venv` symlink at the new path; ran imaging via
`.venv/bin/python -m uvicorn` instead of the `.venv/bin/uvicorn` script to sidestep the
still-broken shebang (a full `uv sync` would have rewritten shared-repo venv state, avoided).
All app processes (api on :3200, worker, imaging on :8000, web on :5173, floor on :5174) were
restarted from the new paths and re-health-checked before continuing. No data or test evidence
from before the move was lost; nothing about the finding below is an artifact of this incident.

## 1. Repo checks (all against the pinned worktree HEADs above)
| Repo | typecheck | lint | test | build |
|---|---|---|---|---|
| invai-contracts | pass | pass (46 files) | **31/31** | n/a |
| invai-ui | pass | pass (54 files) | **24/24** | n/a |
| invai-imaging | ruff: pass ("All checks passed!") | n/a | pytest **102/102** | n/a |
| invai-backend | pass | pass (284 files) | **645/645** | pass (tsup) |
| invai-web | pass | pass (143 files) | **78/78** | pass (vite; chunk-size warning only, pre-existing) |
| invai-floor | pass | pass (73 files) | **86/86** | pass (vite + PWA; chunk-size warning only, pre-existing) |

All six clean on the first try, no retries. Imaging grew from 30 tests at wave 7's gate to 102
(waves 8–9's imaging work: PDF/SVG input, sheet QR, long-PDF cap, personalization, limits).
Backend grew from 591 to 645; web 76→78; floor stayed 86 (its wave-9 work landed in imaging/
contracts, not floor itself).

## 2. Database: reset, migrate, reference data, seed
- `db:reset` then `db:migrate`: **26** rows in `drizzle.__drizzle_migrations` (`0000`–`0025`,
  up from 24 at wave 7 — new: `outbox_dispatched_idx` (T-12-1), `role_level_timeouts` (T-12-2)).
- `db:seed` ran **four** times (initial, before the browser E2E pass, before the floor suite,
  and a final closing reseed), imaging up and worker stopped first each time, all EXIT 0,
  `{"orders":360,"items":~670-672,"transitions":~3871-3878}`, 25 sheets, ~583-584 transfers,
  264 shipments, 108 inventory variants, ~147-151 listings. **Each run took ~25 seconds**
  (was 15–20 minutes at wave 7) — confirms T-13-5 part 1's seed-efficiency fix is live on this
  HEAD.
- Final state left in the shared dev DB: the closing reseed (run after every smoke-check
  mutation below) wiped the manual sheet build, the Nike-titled draft, the PDF-upload test
  design and the NUL-byte regenerate — 360 orders, 26 migrations, current `seed-output.json`.

## 3. E2E suites
Health before each run: API `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`,
imaging `{"ok":true,"vips_version":"8.18.6"}`, web and floor both 200. Backend ran on :3200
(api :3000 was held by another agent's process this whole gate; every suite pointed at :3200
via `E2E_API_URL`/`VITE_API_URL`/`VITE_API_PROXY`, matching the multi-agent-port convention in
`agent-brief.md`).

| Suite | Seed | Result |
|---|---|---|
| `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | fresh seed | **13/13 passed**, first try. Step 6 (vendor portal inbox) and step 11 (Etsy AI draft validates) — both wave-7-gate blocking bugs — now pass clean. |
| Reseed, 65s pause, `pnpm e2e` (invai-web) | fresh seed | **15/15 passed** (`golden-path.spec.ts` 13/13 + `screens.smoke.spec.ts` 2/2: all owner routes clean, and the vendor-portal check clean), first try. |
| Reseed, worker restarted, `pnpm e2e` (invai-floor) | fresh seed | **3/3 passed** (`floor.spec.ts`, `offline.spec.ts`, `press.spec.ts`), first try. |

No flaky retries anywhere in this gate.

## 4. Smoke checks
| # | Check | Result |
|---|---|---|
| 1 | Vendor portal inbox loads (earlier gate bug) | **Pass.** Logged in as `vendor@suncitydtf.test`, `/vendor` renders "Sheet inbox" with a real row (Desert Bloom Tees, 2026-09-25 #25, Sent, 7 transfers, $16.61). Screenshot `gate/1-vendor-portal-inbox.jpg`. |
| 2 | Etsy AI draft passes validation (earlier gate bug) | **Pass.** Generated a fresh Etsy draft for "Lake Powell Weekend" (production partner is now set by default in seed, unlike wave 7). API: `validation:{ok:true,errors:[]}`. UI confirms "✓ Passes every channel rule". Screenshot `gate/2-etsy-ai-draft-passes-validation.jpg`. |
| 3 | Trademark gate blocks a score of 60+ | **Pass.** `ai.trademarkCheck({text:"Nike Air Jordan shirt"})` → `riskScore:99, riskLevel:"high"`. Edited the draft's title to include "Nike Air Jordan" and called `ai.listings.approve` → **409 `HIGH_TRADEMARK_RISK`**, `riskScore:99`, matches `AIR JORDAN`/`NIKE`/`JORDAN` (Nike, Inc.), blocked with no override, exactly per `combineRisk`'s `riskScore >= 60 ⇒ "high"` and the approve-time gate's no-bypass comment. |
| 4 | Compose a gang sheet; header + transfer QRs decode | **Mixed — see finding A below.** Built a fresh 2-sheet batch via `production.batches.build`. Decoded every QR in the resulting sheet PNGs with `zxingcpp` (imaging's own test dependency): **transfer QRs decode correctly** — on the existing sent sheet "2026-09-25 #25", all 7 QR payloads exactly matched that sheet's 7 real `transferId`s. The **header QR did not appear** on either sheet I checked (confirmed a real, reproducible bug, not a fluke — see finding A). A direct, isolated `/compose` call with a short label confirmed the mechanism itself is correct end-to-end (header QR decoded to `"QA9 test #1"`, transfer QR decoded to the placement's `transfer_id`). Screenshot `gate/3-gang-sheet-qr-decode.jpg` (sheet detail page). |
| 5 | A PDF design upload renders | **Fail — see finding B below.** Uploaded a minimal valid PDF as a design print file; QA (`designs.runQa`) failed deterministically with `unreadable: pdf input requires target_dpi`. Screenshot `gate/4-pdf-design-upload-qa-failed.jpg` ("QA: Failed" badge). |
| 6 | A NUL byte in a listing brief doesn't crash | **Pass.** `ai.listings.regenerate({brief:"Make it beachy\u0000 and fun"})` → 200, job queued and completed to `needs_review` with no crash and no 500 anywhere in the API log — confirms T-8-6's `sanitizeInput` oRPC middleware is working on this exact path (`listing_drafts.brief`, named in that commit's own message). |
| 7 | `/livez` and `/readyz` respond | **Pass.** `/livez` → `200 {"ok":true}`; `/readyz` → `200 {"ok":true,"db":true,"redis":true}`. Confirms T-12-2 landed and works. |

### Finding A (not blocking this gate's own suites, but real): header QR silently drops on any realistic multi-order sheet
`invai-imaging/app/compose.py`'s `render_header()` silently returns a blank strip — no QR, no
text, nothing logged — whenever the sheet's label (backend's `filenameHint` =
`sheet.name + " " + all distinct order numbers on the sheet`, capped at 150 chars) needs more
physical width than the fixed `header_height_in` (0.45in) can hold at the 0.33mm/module floor
(`MIN_MODULE_MM`, AC1). Verified directly: the real seeded sheet's actual label
(`"2026-09-25 #25 #1553 113-2323405-1004615 113-2324316-1004628 113-2327049-1004667
3104012987"`, 91 chars from 5 distinct orders) needs a QR whose modules require **0.507in**,
but only 0.45in is available — `header_qr_image()` returns `None` and `render_header()` drops
silently. A short label (`"2026-09-25 #25"` alone, no order numbers) fits fine (0.30in) and
decodes correctly — so the QR-rendering code itself is correct; only realistic (multi-order)
labels overflow the fixed band. Since a gang sheet with only one order per sheet is the
exception, not the rule, this means the header QR — AC2's whole point, "so CADlink (or a
human) can look the job up by scanning the header code" — effectively **never renders on a
real production sheet**, with no error, no warning, nothing in the API/imaging logs to notice
it happened. **Filed for the T-9-2 (sheet-barcode) owner**: either scale the header band to the
label's needed size (bounded), shorten what goes into the label (e.g. sheet id only, not every
order number), or at minimum log a warning when the header is dropped instead of doing it
silently.

### Finding B (blocking): PDF design uploads can never pass QA
`invai-imaging/app/qa.py`'s `check()` calls `load(path, access="sequential")` with no
`target_dpi` argument, and `QACheckRequest` (the `/qa/check` endpoint's own input model, in
`app/main.py`) has **no `target_dpi` field at all** for a caller to supply one — `invai-backend`'s
`qaCheck()` client call only ever sends `target_width_in`/`target_height_in`. But
`app/vips.py`'s generic `load()` raises `ImageError("pdf input requires target_dpi")`
immediately for any `.pdf` input when `target_dpi` is `None` — which it always is here, so
every PDF-format design print file fails QA 100% of the time, regardless of content, size, or
target dimensions. Confirmed live: uploaded a valid single-page PDF as a design placement,
`designs.runQa`'s job finished with `qaStatus:"failed"`,
`issues:[{"code":"unreadable","severity":"error","message":"pdf input requires target_dpi"}]`.
Grepped the whole imaging app for `target_dpi` — it is defined once (`vips.py`) and used
nowhere else; `compose.py`'s `_prepare_design()` (used when a sheet is actually built) has the
exact same gap, so a raw PDF placed directly on a sheet would fail the same way, though in
practice the backend's own print-file pipeline rasterizes PDFs to PNG before compose ever sees
them — QA is the one path that hands a raw PDF straight to `load()`. This is exactly the
"target DPI" T-9-1 card was supposed to close (`B-78`: "PDF and SVG input at target DPI" —
evidence cited in that card is `app/vips.py:25-32`, `no pdfload`); it landed the loader-level
support but never wired a caller to actually pass `target_dpi` for the QA check. **Filed for
the T-9-1 (pdf-svg) owner**: `qa.check()` needs to compute and pass a `target_dpi` (e.g. from
`target_width_in`/`target_height_in` against a reasonable default page size, or just a fixed
QA-preview DPI) whenever the input is PDF, and `QACheckRequest` should probably expose the
field directly so a caller with real target dimensions doesn't have to guess.

## Cleanup
- Worktrees: all six `gate9/<repo>` worktrees removed (`git worktree remove --force` from each
  origin repo); `git worktree list` in every repo now shows only its own primary worktree (and,
  in backend/web/floor, other agents' own unrelated `-t134` worktrees, left untouched). The now
  empty `invai/gate9/` directory was removed.
- App processes this gate started (imaging on :8000, api and worker via `tsx watch` on :3200,
  web on :5173, floor on :5174) were all stopped by their recorded PIDs.
  `lsof -iTCP:3200 -iTCP:5173 -iTCP:5174 -iTCP:8000` confirmed empty afterward. **Not touched,
  not mine:** the process already holding :3000, and other agents' 31xx-range dev processes and
  `-t134` worktree processes.
- Dedicated gate test DB `invai_test_gate9` dropped. `invai_test_t122` dropped (per
  instructions). `invai_test_t86` did not exist (nothing to drop). `invai_test_t81` — not on
  the instructed drop list, not mine, **left untouched**. `invai_test` untouched throughout.
- Infra (Docker) left running: 4/4 local containers healthy.
- The dev DB is left freshly reset (26 migrations) and seeded (360 orders, ~147-151 listings) —
  this gate's own smoke-check mutations (the manual sheet build, the Nike-titled test draft, the
  PDF-upload test design, the sample-art test file, the NUL-byte regenerate) do not persist; the
  closing reseed in §2 wiped them all. `seed-output.json` is current in `invai-backend`.
- Nothing was pushed. This gate's own output (`invai-docs/waves/9/gate.md` and
  `invai-docs/waves/9/gate/`) is committed here with a pathspec.

## Recommendation
**Do not push yet.** Every repo's typecheck/lint/test/build is green against the pinned wave
6–9 HEADs (contracts 31/31, ui 24/24, imaging ruff + 102/102 pytest, backend 645/645, web
78/78, floor 86/86, all builds clean), the DB reset/migrate/seed cycle is clean and fast
(T-13-5 part 1 confirmed — ~25s vs wave 7's 15–20 min), reaches migration 26, and **all three**
golden-path suites are fully green for the first time in this gate's history (API 13/13,
browser 15/15, floor 3/3) — both of wave 7's blocking bugs (vendor portal inbox, Etsy AI draft
validation) are confirmed fixed. `/livez`/`/readyz` (T-12-2) and the NUL-safety boundary
(T-8-6) both work as designed.

But two of the seven wave 6–9 smoke checks are not clean: **finding B** (PDF design uploads
always fail QA, one exact gap: `qa.check()` never computes/passes `target_dpi`) is a hard,
100%-reproducible failure of a stated smoke check and should block push until the T-9-1 owner
fixes it — it's a small, precisely-located fix. **Finding A** (header QR silently drops on any
realistic multi-order sheet) doesn't fail any of this gate's own automated suites (they only
exercise deep-linked/API paths, never scan the printed sheet), but it does fail the smoke
check as literally asked ("compose a gang sheet, and the header plus transfer QRs decode") and
quietly defeats a shipped, load-bearing feature (AC2) with no error anywhere — recommend the
T-9-2 owner take it before push too, even though it's lower urgency than finding B. Neither
bug was retried; both are deterministic and root-caused to one exact spot each, not
environmental. Once both are fixed, a short re-run of just the affected checks (imaging pytest
for the QA fix, one more compose + QR-decode pass for the header fix) should be enough — no
full re-gate needed.
