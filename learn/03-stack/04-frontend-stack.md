# Lesson 3.4 — React, TanStack, Vite, Vitest and Playwright

## 1. In one sentence
Both frontends (`invai-web`, the dashboard, and `invai-floor`, the tablet PWA) are plain Vite +
React single-page apps using the TanStack family (Router, Query, Table, Virtual) for routing,
server state and data grids — a deliberately boring, portable choice over a full meta-framework
like Next.js, tested with Vitest for units and Playwright for everything that needs a real
browser.

## 2. Why it exists
`invai-docs/research/09-tools-frontend.md` opens with a warning worth repeating verbatim:
"Several libraries are a major version past what AI assistants mostly learned: React Router 8,
Vite 8, TanStack Table 9... Tell your coding assistant the exact versions, or it will write
outdated APIs." This lesson explains *why* each of these specific, newer-than-you'd-expect
choices was made, so the "why" survives even after you've forgotten the exact API.

## 3. How it works

### Vite + React SPA — chosen over Next.js on purpose
`invai-docs/research/09-tools-frontend.md:15-33` scores **Vite 8 + React 19 SPA (with TanStack
Router)** at **9/10** against **Next.js 16** (7/10): "Fastest dev loop. Hosts on any static
host or CDN... No gap between server and client code. You don't need SSR behind a login." The
key phrase is *behind a login* — every screen in `invai-web` and all of `invai-floor` requires
a signed-in session, so server-side rendering's main benefit (fast first paint for an
anonymous visitor) doesn't apply. Next.js remains the documented runner-up specifically for
"if you want the frontend to also be your BFF" (backend-for-frontend) — not a need InvAI has,
since oRPC already plays that role. Astro and SvelteKit/Nuxt were ruled out early: wrong shape
for a SPA dashboard, or a smaller React-ecosystem fit (less assistant fluency, fewer available
component libraries).

### TanStack Router, Query, Table and Virtual — one family, headless by design
- **TanStack Router** gives typed routes; a route's params and loader data are typed from the
  route definition itself, the same "generate types from one declared shape" idea as oRPC's
  contract.
- **TanStack Query** is the data-fetching/caching layer sitting on top of the oRPC client — see
  `invai-web/src/routes/accept-invite.$invitationId.tsx:3,44,49` for a real `useQuery` call
  against the typed client.
- **TanStack Table** (`invai-docs/research/09-tools-frontend.md:53-68`) scored **9/10**,
  specifically because it's **headless**: "matches shadcn exactly... You build column resize,
  pinning and virtualization yourself" — the tradeoff accepted over AG Grid Community (8.5,
  ships more built-in but with its own theming system to reconcile) because InvAI's UI already
  has its own design system (`@invai/ui`) to style against, not a grid vendor's.
- **TanStack Virtual** pairs with Table so a list of thousands of order rows renders only the
  visible slice.

All four are on notably newer majors than most training data has seen (Table v9, Router
v1.170) — which is exactly why `read-before-change`'s library table calls out
`@tanstack/react-table/skills/*/SKILL.md`: the package itself ships an agent-readable migration
guide (`migrate-v8-to-v9`) precisely because this mismatch is expected.

### Vite 8 — the build tool under both apps
Vite handles dev server, HMR and production bundling for both `invai-web` and `invai-floor`.
Floor additionally uses `vite-plugin-pwa` (research score **9/10**, "manifest and precaching
with zero config") to make the tablet app installable and offline-capable — module 06 covers
the offline scan queue this enables.

### Vitest and Playwright — unit vs. real-browser, and why both are needed
`invai-docs/research/06-tools-backend.md:149-163`'s dev-tooling table is blunt: **Vitest** is
"the standard for TypeScript" with no real competing recommendation, and **Playwright** "can
emulate tablets" — a specific, concrete reason it beat Cypress or a bare `jsdom` approach for
InvAI: the floor app's tests need to simulate an actual tablet viewport and a keyboard-wedge
barcode scanner's rapid-keystroke input pattern, which only a real browser engine reproduces
faithfully.

In practice: `invai-backend/vitest.config.ts:1-17` configures tests to run against the **real**
`invai_test` Postgres database (`globalSetup`, `fileParallelism: false` — tests share one DB
and must run one file at a time to avoid cross-test interference) rather than mocking the
database — this is deliberate: an RLS bug can only be caught by a real Postgres enforcing real
policies, never by a mocked query layer. `invai-web/playwright.config.ts:1-30` runs true
end-to-end: a live `:5173` dev server, a live `:3000` API, a live `:8000` imaging service and a
freshly seeded database — this is what "exercised for real" (`CLAUDE.md`'s definition of done)
actually means at the E2E layer.

## 4. In our code
- `invai-web/package.json`, `invai-floor/package.json` — pinned versions:
  `@tanstack/react-router@^1.170.39`, `@tanstack/react-table@^9.2.4`, `vite@^8.3.0`,
  `vitest@^5.0.1`, `@playwright/test@^1.63.0`.
- `invai-web/src/routes/accept-invite.$invitationId.tsx:3,44,49` — a real `useQuery` call
  against the typed oRPC client.
- `invai-backend/vitest.config.ts:1-17` — tests against the real `invai_test` database,
  `fileParallelism: false`.
- `invai-web/playwright.config.ts:1-30` — the real-stack E2E setup, including the comment
  explaining why `.e2e-out` lives outside `invai-web/` (a live dev server watching the whole
  tree would reload on every trace/report file write otherwise).
- `invai-docs/research/09-tools-frontend.md:15-68` — the meta-framework and data-grid
  comparison tables this lesson draws from.

## 5. What it uses
- **React 19.3** — the UI library; `@invai/ui` (module 02) is the shared component layer both
  apps consume.
- **Vite 8** — dev server and bundler for both frontends; `vite-plugin-pwa` adds offline
  capability to `invai-floor`.
- **TanStack Router/Query/Table/Virtual** — typed routing, server-state caching, headless data
  grids, and virtualized lists, all from one family that composes cleanly rather than one
  all-in-one framework.
- **Vitest 5** — unit and integration tests in every TS repo, run against real dependencies
  (Postgres) where it matters.
- **Playwright 1.63** — real-browser E2E, including tablet-viewport emulation for
  `invai-floor`.

## 6. Try it yourself
1. Run `cd invai-web && export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH" && pnpm vitest run --reporter=dot 2>&1 | tail -n 20` and note how fast it is compared to a Playwright run — this is the "unit tests for logic, Playwright for what needs a real browser" split in practice.
2. Open `invai-web/src/routes/__root.tsx` and find where TanStack Router's route tree is
   defined — compare it to a React Router route you may have seen before; note what's typed
   automatically versus what you'd have to type by hand in a simpler router.
3. Read `invai-web/playwright.config.ts`'s comment about `.e2e-out` living outside
   `invai-web/` — this is a real lesson the project hit (cited in the config itself); try to
   explain in one sentence why a live dev server watching its own test-output folder would
   cause a problem.

## 7. Common mistakes
- Writing TanStack Table v8-style code (common in most AI training data and older tutorials)
  against the installed v9 — check the package's own `skills/*/SKILL.md` migration guide
  first, per `read-before-change`.
- Mocking the database in a Vitest file to make tests "faster." `invai-backend/vitest.config.ts`
  deliberately runs against real Postgres so RLS bugs are caught; a mocked query layer cannot
  catch "a table is missing its RLS policy."
- Running Playwright against `invai-web` while another agent's `tsx watch` process is mid-
  restart — `CLAUDE.md`'s lessons log notes this causes flaky "died mid-restart" failures;
  retry rather than assume the feature is broken.

## 8. Check yourself
<details>
<summary>1. Why did Vite + React SPA beat Next.js for InvAI, when Next.js scored well on
"assistants know it best"?</summary>

Every screen in both frontends sits behind a login, so SSR's main benefit — fast first paint
for an anonymous visitor — doesn't apply; a plain SPA avoids RSC/caching complexity with no
real payoff for this use case.
</details>

<details>
<summary>2. TanStack Table is "headless." What does that mean, and what did InvAI trade away
by choosing it over AG Grid Community?</summary>

Headless means it only manages data/state (sort, filter, selection) and renders nothing
itself — you build the actual markup and styling. InvAI traded away AG Grid's built-in
virtualization, CSV export and polished default styling, in exchange for a grid that matches
`@invai/ui`'s own design system exactly instead of fighting a vendor's theming system.
</details>

<details>
<summary>3. Why does `invai-backend/vitest.config.ts` set `fileParallelism: false`?</summary>

Every test file shares one real `invai_test` Postgres database; running files in parallel
would let tests from different files interfere with each other's rows, so files run one at a
time instead.
</details>

## 9. Words to know
- **SPA (single-page app)** — a frontend that loads once and then swaps views client-side,
  without full-page server reloads; the opposite of server-rendering each page on request.
- **Headless (UI library)** — a library that manages behavior/state but renders no markup of
  its own; you supply the visual layer.
- **HMR (hot module replacement)** — Vite's dev-time feature that swaps changed code in the
  running browser without a full page reload.
