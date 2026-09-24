---
name: build-dashboard-screen
description: Build or change a screen in invai-web (owner/office/designer dashboard or the vendor portal) with TanStack Router and Query over the typed oRPC client, @invai/ui components, loading/empty/error/partial states, realtime refresh, en/es, light and dark, 390 px, and Playwright screenshots you looked at. Use for "new page", "screen", "dashboard", "table view", "form", "web UI".
---

# Build a dashboard screen

A web screen that shows what's urgent first, handles every state, works in English and Spanish, light and dark, at phone width where required, and was looked at in screenshots before the report.

## When to use
- A card assigns `invai-web/**` work (web-engineer) with a UX spec from the product-designer in `invai-docs/design/`.
- A missing `@invai/ui` component: build it locally in `invai-web/src/components/`, report it, and the designer adds it to the kit (`add-ui-component`). Never edit `invai-ui`.
- A missing procedure: ask the tech lead for an architect change; never fake data.

## Steps
1. **Read** the card and UX spec, `invai-web/README.md`, `src/lib/nav.ts`, `src/lib/{rpc,upload,format,errors,me,realtime}.ts`, `src/components/{page,states}.tsx`, `invai-ui/README.md`, the procedures you call in `invai-contracts/src/contract/<domain>.ts`, and a similar route (e.g. `src/routes/_app/settings/audit.tsx` for an infinite list).
2. **Route** as a file in `src/routes/_app/<area>/<name>.tsx` with `createFileRoute("/_app/<area>/<name>")`. `src/routeTree.gen.ts` regenerates on `pnpm dev`. Add the nav entry in `SHOP_NAV` or `VENDOR_NAV` (`src/lib/nav.ts`) with the permission that gates it; vendor orgs see only the portal.
3. **Data** with the typed client: `useQuery(orpc.<ns>.<proc>.queryOptions({ input }))`, lists with `orpc.<ns>.list.infiniteOptions(...)` and `getNextPageParam: (last) => last.nextCursor ?? undefined`, mutations with `orpc.<ns>.<proc>.mutationOptions()` and invalidation by `orpc.<ns>.key()`. Page size ≤ 200.
4. **Realtime:** if the data changes from workers or other users, make sure its event is mapped in `keysForEvent()` (`src/lib/realtime.ts`).
5. **Every state:**
   - loading: `SkeletonRows` or skeletons, never a blank page;
   - empty: `EmptyState` with the next action in plain words;
   - error: `ErrorState` (NOT_IMPLEMENTED shows the calm "coming soon" look automatically);
   - partial: some rows failed or a job is running (`useJob` for job progress).
   Use `QueryView` from `src/components/states.tsx` where it fits.
6. **Urgency first.** Ship-by, at-risk and overdue lead every order view (`ShipByBadge`, `StatusBadge` from `@invai/ui`); status colors mean the same thing everywhere and never rely on color alone.
7. **Formatting:** money with `Money`/`formatMoney` (integer cents), inches with `formatInches`, dates with `formatDate`/`formatDateTime`, order numbers with `orderLabel()` (adds one `#`), people with `firstName()` in lists (`src/lib/format.ts`).
8. **Permissions:** hide or disable actions with `useCan()` (`src/lib/me.ts`) using the procedure's permission. Never rebuild buyer PII the backend masked.
9. **Actions:** undo toast (`toast` from `@invai/ui`) for reversible actions; `confirm-dialog.tsx` for destructive or costly ones (cancel order, buy a label batch, approve a high-trademark-risk listing). Handle 429 and 503: show "try again in N seconds" from `Retry-After`, don't spam retries (`shouldRetry` in `src/lib/errors.ts`).
10. **Uploads** only through `uploadFile()` (`src/lib/upload.ts`): presign, direct PUT, one retry with a fresh URL on 403. The signature binds type and size.
11. **Text:** `t("key", "Default English")` inline, then `pnpm i18n` to regenerate `src/i18n/{en,es}.ts` and write real Spanish (`write-plain-language-copy`). AI and assistant output renders as text or sanitized Markdown; no `dangerouslySetInnerHTML`.
12. **Analytics** only from the taxonomy (`instrument-analytics-event`).
13. **Check:** `pnpm typecheck && pnpm lint && pnpm test && pnpm build`.
14. **Look at it.** With the stack running on a fresh seed, take Playwright screenshots of the changed screens in light and dark, en and es, and at 390 px for Today and Orders (no horizontal scroll), then open each image. Add the route to `SHOP_ROUTES` in `e2e/screens.smoke.spec.ts` only if the card gives you e2e (qa-engineer owns the suites).
15. **E2E:** `pnpm e2e` (golden path plus screens smoke) must stay green with no console errors or failed requests.

## Rules (MUST / MUST NOT)
- MUST NOT edit `invai-ui`, `invai-contracts` or the backend; MUST NOT fake a missing procedure.
- MUST NOT remove the `vite.config.ts` dedupe of react, i18next and TanStack across linked repos (it breaks dev with "invalid hook call"), or the `@source "../../invai-ui/src";` line in `src/styles.css`.
- MUST keep targets at least 24 × 24 px and the screen keyboard-usable; forms allow paste and password managers.
- MUST check library APIs in `node_modules` (TanStack Table v9, Vite 8, AI SDK v7, Zod v4 are newer than training data).
- MUST get product-designer as co-reviewer for any UI change, qa-engineer for golden-path screens.

## Done when
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` pass in `invai-web`.
- Screenshots (light/dark, en/es, 390 px where required) exist and were looked at; paths are in the report.
- Loading, empty, error and partial states were each seen.
- `pnpm e2e` is green on a fresh seed.

## References
- `invai-web/README.md`, `.claude/agents/web-engineer.md` ("Things that bite")
- `invai-ui/README.md` (component list)
- `invai-docs/research/12-security-quality-playbook.md` §3.7 (WCAG 2.2), §3.8 (i18n); `11-platform-scale-playbook.md` §6.1 (web JS ≤ 250 KB gzip)
- Related: `add-ui-component`, `instrument-analytics-event`, `write-plain-language-copy`, `ux-audit`
