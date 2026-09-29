# Wave 23: P2 sweep, part 2: screens, floor, imaging, AI polish and E2E coverage

- Dates: planned; starts after the wave 22 gate
- Goal (user outcome): every backend capability from wave 22 has a screen (no dead procedures), the floor has QC reasons, the maintenance block, bin locations and a camera scanner, gang sheets get the remaining print-quality controls, assistant answers read cleanly in both languages, and the role, Spanish and offline suites plus visual/contract/i18n drift checks run on every change.
- Sources (backlog): B-22 rest (property tests, axe), B-34 (scale seed profiles), B-38, B-41, B-81 rest (buyer-photo upload), B-97 rest, B-103 rest, B-105 rest (camera scanner), B-107 (bundle size), B-114, B-131, B-132, B-134, B-135, B-138, B-142, B-162 (web), B-165, and the web/floor halves of B-25, B-32, B-35, B-102.
- Plan reviewed by: product-manager (2026-09-28, approve with changes: B-131 spec step by PM first), architect (2026-09-28, approve; notes for the buyer-photo upload contract dependency).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-23-1 Web: SCAN forms, address check, vendor resend, settings toggles, maintenance and QC-reason reports, buyer-photo upload, bundle split (B-25, B-35, B-81, B-102, B-107, B-162 web halves) | web-engineer | sonnet | reviewer (opus) + product-designer, security-reviewer (upload: files) | ui, files | planned |
| T-23-2 Floor: QC fail reasons, maintenance block, transfer-age warning, bin in pick list, camera scanner, bundle (B-32, B-35, B-105, B-107 floor) | floor-engineer | sonnet | reviewer (sonnet) + product-designer, qa-engineer | floor-correctness, ui | planned |
| T-23-3 Imaging polish and film-use metric (B-103 rest, B-41) | imaging-engineer | sonnet | reviewer (opus) + architect (bounds in contract) | files | planned |
| T-23-4 AI and market polish: markdown and footer, stream close, mock follow-ups, eval cleanup, detrended seasonality in code, shared ConfidenceBadge adoption (B-114, B-131, B-132, B-135, B-165; B-134 via a product-designer grant) | ai-engineer (+ backend-engineer market for the B-131 engine by grant; never `specs/**`) | sonnet | reviewer (sonnet) + product-designer (badge) | ai | planned |
| T-23-5 E2E and test coverage: roles, Spanish, offline replay, clickIfShown, property tests, axe, visual regression, runtime contract test, i18n drift, scale seed profiles, market tool latency (B-22 rest, B-34, B-38, B-97 rest, B-138, B-142) | qa-engineer | sonnet | feature owners (web, floor) + reviewer (opus) | — | planned |

## Order
- **Prerequisite (PM plan review):** the product-manager writes the B-131 Step 3 formula change in `specs/market-signals.md` before T-23-4 starts; T-23-4 implements it.
- T-23-3, T-23-4, T-23-5 can start at once; T-23-1 and T-23-2 after wave 22 is pushed. At most 3 builders at once.

## Integration gate
- [ ] Fresh reset, migrate, seed; `run-golden-path`; new role/Spanish/offline suites green
- [ ] Screens looked at in en/es; floor at 1280×800
- [ ] Pushed to `main`

## Handoff from wave 22 (2026-09-29, tech lead)
- **Wave 22 state:** every card is approved (reviews in `waves/22/reviews/`); the only one still open is T-22-4's qa-engineer floor co-review, written by the wave 22 gate. The gate (qa-engineer) was **still running** at handoff: check `waves/22/reviews/gate.md`. **Nothing from wave 22 is pushed yet.** Once `gate.md` shows the pass, push invai-contracts (`0f2f413`, `9e8ea0c`), invai-backend (`faff2b9`..`04e72a0`, migrations 0030–0035) and invai-docs (includes `4a8da1a` decision 0018, `c0e9e5a`, `5f2ed51`), then tick the wave 22 gate boxes.
- **Don't push:** infra `3dbb899` and web `c1d53a8` (wave 24 T-24-1). They still need the security-reviewer and web-engineer co-reviews. With `c1d53a8`, plain `pnpm build` in invai-web needs `VITE_API_URL`.
- **First card to start:** B-205 (backend-foundation, sonnet). Backend tests use Redis DB 0 (`src/env.ts` redirects Postgres but not Redis), so BullMQ tests race any dev worker; this is the root of the "flakes" seen since wave 20. It's small; run it before or alongside T-23-3/T-23-4/T-23-5. Until then every run sets its own `REDIS_URL` (see `team/agent-brief.md`). T-23-1/T-23-2 start after wave 22 is pushed.
- **Add to T-23-1 (web):** B-206 (alert kind `vendor_email_failed`: architect adds the contract kind first, then the vendors switch and web mapping; also read `titleEs`/`messageEs` at `index.tsx:405`), and the Resend button for `unknown`/`failed` deliveries.
- **Add to T-23-2 (floor):** show `station_maintenance` blocks, including on offline replay (backend blocks by `scannedAt`, `03d780e`).
- **Open follow-ups:**
  - B-199: search under RLS (architect decision; T-22-2 AC5 descoped).
  - B-200: privacy purge misses `address_verifications`.
  - B-201: market test clock leak.
  - B-202: mailer `toHash` unkeyed.
  - B-203 (S-39 Low): tenant columns without an FK, e.g. `createDesign`.
  - B-204: the seed has no bins or transfer ages.
  - T-22-5 non-blocking notes (in its report): `updateExisting` doesn't lock the order row, SMTP socket-error retries could rarely double-send, `mergeTotals` ignores a real change to 0.
- **Environment:** leftover dir `invai-backend-T-22-1-rev` (the tech lead wasn't permitted to delete it); API :3142 (tsx watch since 2026-09-26) and vite :5183, owners unknown. Earlier "stalled" agents can still be alive: check `ps` and `git log` before relaunching (lesson 2026-09-29).
