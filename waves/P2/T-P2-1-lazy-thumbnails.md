# T-P2-1: Catalog grid loads thumbnails only when on screen (P1 gate fix 1)

| Field | Value |
|---|---|
| Wave | P2 |
| Scope ref | `always-in-scope: bug` (P1 gate failure, `waves/P1/reports/gate-rootcause.md` §1; regression exposed by T-P1-4 / B-209) |
| Spec | `waves/P1/reports/gate-rootcause.md` §1 |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (no contract change, no new screen or component in invai-ui; decision 0019) |
| Risk flags | none (UI behavior only, no new copy expected) |
| Model | sonnet |
| Depends on | nothing (dev DB already has 40/40 design previews from T-P1-4) |

## Root cause (QA, confirmed by code reading)
- `invai-web/src/routes/_app/catalog/designs.index.tsx:176` renders one `<SignedImage>` per design card for the whole first page (~40). Each fires `files.downloadUrl` (`src/components/signed-image.tsx:7-16`). Before T-P1-4 every `previewKey` was null, so none fired.
- ~40 requests queue behind Chrome's 6-connection cap; the e2e click navigates away and aborts the rest; `watchPage()` flags each `net::ERR_ABORTED` (correctly). The `analytics/designLifecycle` call (`designs.index.tsx:90`) is aborted by the same queue.

## Owned paths (edit)
- `invai-web/src/routes/_app/catalog/designs.index.tsx`
- `invai-web/src/components/signed-image.tsx` (if you change shared behavior, check every call site: `grep -rn SignedImage invai-web/src`)
- A new hook file under `invai-web/src/lib/` or `src/components/` if you need one (name it in the report)
- Generated i18n (`src/i18n/*.ts`, `scripts/i18n-es.json`) only if you add a string

## Read-only paths
- `invai-web/e2e/**` (QA; T-P2-3 changes `e2e/helpers/ui.ts`), `invai-backend/**` (T-P2-2), `invai-contracts/**`, `invai-ui/**`, everything else.

## Acceptance criteria
1. On `/catalog/designs`, a card requests its signed URL only when it is in or near the viewport (for example IntersectionObserver with a modest `rootMargin`). Off-screen cards render a static placeholder that is **not** `[data-slot=skeleton]` and not `.animate-spin` (so `settled()` can finish).
2. At 1440×900 on the dev DB (40 designs with previews), the first load fires at most the visible cards plus one row of `files.downloadUrl` calls (count them with a Playwright script or devtools; report the number). Scrolling down loads the rest; the images are real thumbnails.
3. Clicking a design right after the list settles produces no aborted requests: `market.spec.ts:197` (AC32) and `screens.smoke.spec.ts` pass with **no change to any allow-list or to `e2e/**`**.
4. Other `SignedImage` users (design detail, order drawer, anything the grep finds) behave as before, or lazily only where that is safe; say which in the report.
5. No bulk signed-URL endpoint (that would be a contract change; out of scope).

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 30` (build needs `VITE_API_URL` set, as the gate does).
- Slot: you have the shared **API :3000 + web :5173** slot (the web CSP allows only API :3000, B-220). Start `pnpm dev:api` and `pnpm dev:worker` in `invai-backend` and `pnpm dev` in `invai-web`, record every PID, and stop all of them before reporting (the gate needs these ports next). Don't reseed or reset the dev DB.
- `cd invai-web && pnpm e2e e2e/market.spec.ts e2e/screens.smoke.spec.ts --reporter=line 2>&1 | tail -n 30` → pass.
- Screenshots of `/catalog/designs` at 1440 px and 390 px, en and es, before and after scrolling; look at them.

## Out of scope
- Contract or backend changes, a bulk URL endpoint, virtualization libraries (no new dependency), e2e helper changes (T-P2-3).

## Budget
- About 2 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths in `invai-web` (`git add <paths>`). Don't push. Report: `invai-docs/waves/P2/reports/T-P2-1.md` (at most 60 lines, `verify-and-report` format, PIDs started and stopped).
