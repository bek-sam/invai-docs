# Wave 23: P2 sweep, part 2: screens, floor, imaging, AI polish and E2E coverage

- Dates: planned; starts after the wave 22 gate
- Goal (user outcome): every backend capability from wave 22 has a screen (no dead procedures), the floor has QC reasons, the maintenance block, bin locations and a camera scanner, gang sheets get the remaining print-quality controls, assistant answers read cleanly in both languages, and the role, Spanish and offline suites plus visual/contract/i18n drift checks run on every change.
- Sources (backlog): B-22 rest (property tests, axe), B-34 (scale seed profiles), B-38, B-41, B-81 rest (buyer-photo upload), B-97 rest, B-103 rest, B-105 rest (camera scanner), B-107 (bundle size), B-114, B-131, B-132, B-134, B-135, B-138, B-142, B-162 (web), B-165, and the web/floor halves of B-25, B-32, B-35, B-102.
- Plan reviewed by: product-manager (2026-09-28, approve with changes: B-131 spec step by PM first), architect (2026-09-28, approve; notes for the buyer-photo upload contract dependency).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-23-1 Web: SCAN forms, address check, vendor resend, settings toggles, maintenance and QC-reason reports, buyer-photo upload, bundle split (B-25, B-35, B-81, B-102, B-107, B-162 web halves) | web-engineer | sonnet | reviewer (opus) + product-designer, security-reviewer (upload: files) | ui, files | planned |
| T-23-2 Floor: QC fail reasons, maintenance block, transfer-age warning, bin in pick list, camera scanner, bundle (B-32, B-35, B-105, B-107 floor) | floor-engineer | opus | reviewer (sonnet) + product-designer, qa-engineer | floor-correctness, ui | planned |
| T-23-3 Imaging polish and film-use metric (B-103 rest, B-41) | imaging-engineer | sonnet | reviewer (opus) + architect (bounds in contract) | files | planned |
| T-23-4 AI and market polish: markdown and footer, stream close, mock follow-ups, eval cleanup, detrended seasonality in code, shared ConfidenceBadge adoption (B-114, B-131, B-132, B-135, B-165; B-134 via a product-designer grant) | ai-engineer (+ backend-engineer market for the B-131 engine by grant; never `specs/**`) | opus | reviewer (sonnet) + product-designer (badge) | ai | planned |
| T-23-5 E2E and test coverage: roles, Spanish, offline replay, clickIfShown, property tests, axe, visual regression, runtime contract test, i18n drift, scale seed profiles, market tool latency (B-22 rest, B-34, B-38, B-97 rest, B-138, B-142) | qa-engineer | fable | feature owners (web, floor) + reviewer (opus) | — | planned |

## Order
- **Prerequisite (PM plan review):** the product-manager writes the B-131 Step 3 formula change in `specs/market-signals.md` before T-23-4 starts; T-23-4 implements it.
- T-23-3, T-23-4, T-23-5 can start at once; T-23-1 and T-23-2 after wave 22 is pushed. At most 3 builders at once.

## Integration gate
- [ ] Fresh reset, migrate, seed; `run-golden-path`; new role/Spanish/offline suites green
- [ ] Screens looked at in en/es; floor at 1280×800
- [ ] Pushed to `main`
