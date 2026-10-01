# PM review: wave P2 plan

**Verdict: approve** (T-P2-1..3)

## T-P2-1..3 checked
- Scope refs valid: all three cite `always-in-scope: bug`, each tied to a real gate failure in
  `waves/P1/reports/gate-rootcause.md` (§1 for T-P2-1, §2 for T-P2-2) or the test helper that masked it
  (T-P2-3). These are real regressions on the golden path, not scope creep.
- Ownership respected: T-P2-1 (web-engineer) owns only `designs.index.tsx`/`signed-image.tsx`; T-P2-2
  (backend-engineer catalog) owns `modules/catalog/**` plus three narrow, named grants (imaging client's
  `preview` method, one log line in `production/router.ts`, a test in `orders/`); T-P2-3 (qa-engineer) owns
  only `e2e/helpers/ui.ts`. No overlap with each other or with busy paths.
- T-P2-2's AC0 (prove the cause with numbers before fixing) is the right discipline — the P1 hand-off's
  contention hypothesis was explicitly unproven; good that the card won't ship a fix without first confirming
  or refuting it.
- `files` flag on T-P2-2 correctly pulls in `security-reviewer` (decision 0019): `isCompanyKey` checks move
  with the code. T-P2-1 and T-P2-3 correctly carry no risk flags (UI behavior with no new copy; test code
  only).
- Budgets (2h/3h/1h) are close to the "2–3 hours, one owner" guidance; T-P2-2's 3h is reasonable given AC0's
  measurement work.
- No bulk signed-URL endpoint and no contract change in T-P2-1 (explicitly out of scope) — correct; that
  would need the architect and isn't justified yet.

## Slots 4 and 5: ranking (full detail in `product/backlog-ranking.md`, 2026-10-01 section)
**Top pick, T-P2-4: B-223 + B-224** — order-drawer timeline and Today alert bodies show raw English state
strings/keys under the Spanish UI. Owner: backend-engineer (orders + today) + web-engineer. Acceptance: given
the UI is set to Spanish, when a presser/office user opens an order with a timeline transition or sees a
Today alert, the backend returns a translation key/code (not raw English) and the web app renders the
Spanish string, with no raw key or English fallback visible in either language at 1440px and 390px.

**Top pick, T-P2-5: Today actions jobId re-queue after 3 failures** — a build job that fails three times keeps
its `jobId`, so the Today actions panel can't re-queue that day and stays hidden. No B-id yet (`waves/24/wave.md`
L53, `waves/A2/wave.md` T-A9 reviewer). Owner: backend-engineer (today). Acceptance: given a shop's Today
build failed 3 times today, when the next build attempt runs (retry or the next scheduled build), it gets a
fresh jobId and the Today panel is populated again, instead of staying hidden until the next calendar day.

**Alternates:** 1) B-230 (Profit v2 losing orders shows Units 0/Revenue $0) — needs a verify-first step before
it's confirmed as a bug, not just a small fix. 2) B-235's Spanish-correctness half (pre-v6 assistant tools
answer in English under es) — matches the Spanish-correctness preference but is a legacy code path with a
partial mitigation already, and carries the `ai` risk flag (extra co-review).

**Not recommended for these two slots:** B-231 and B-132 both need the architect as a second owner (contract
enum shaping / a vendor-library decision) before a single small card can close them — hold for a wave where
the architect has a slot. invai-ui follow-ups are product-designer's repo, not these two engineering slots;
the es money group-separator item inside that bundle is worth its own card next wave. B-227 excluded per the
tech lead's own instruction (no recurrence since one A1 occurrence).
