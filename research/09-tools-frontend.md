# InvAI Frontend Stack Research (as of 2026-09-23)

**How I checked the facts.** WebSearch was already used up for this session (200/200), so I pulled numbers straight from the source:
- npm registry: latest version and license for each package.
- npm downloads API: downloads for the last week.
- GitHub REST API: star counts and last-push dates.
- Official pricing pages, fetched with WebFetch: AG Grid, MUI, Handsontable, Polotno, IMG.LY, STRICH, Scandit, CodeRabbit, Linear, GitHub Actions docs, Next.js deploy docs, TanStack Start docs.

Anything marked **[UNVERIFIED]** comes from memory and was not checked in this session. Star counts are rounded ("k"), and downloads are per week.

**Version note.** Several libraries are a major version past what AI assistants mostly learned: React Router 8, Vite 8, TanStack Table 9, Jotai 3, MUI 9, Mantine 9, AI SDK 7, Storybook 10, Astro 7. Tell your coding assistant the exact versions, or it will write outdated APIs.

---

## 1. Meta-framework

| Option | Latest | Stars | Weekly dl | License | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **Vite + React SPA (+ TanStack Router or React Router in SPA mode)** | vite 8.3.0 | 83.0k | 131M | MIT | Fastest dev loop. Hosts on any static host or CDN. Clean fit for a PWA via vite-plugin-pwa. No gap between server and client code. You don't need SSR behind a login. | You wire routing, auth and code-splitting yourself. You need a separate API/BFF (you probably have one anyway). | **9** |
| Next.js 16 (App Router) | 16.3.6 | 142.4k | 42.7M | MIT | Assistants know it best. Server actions and route handlers act as a BFF. The official docs say Node/Docker self-hosting supports "All" features. | RSC/caching adds complexity with no payoff behind a login. PWA and offline setup is clumsier (Serwist). Only Vercel and Bun are "verified adapters"; Cloudflare and Netlify adapters are still in progress (per Next.js docs). | 7 |
| React Router (framework mode, ex-Remix) | **8.4.0** (not v7) | 56.6k | 40.3M | MIT | Can run as SPA or SSR. Loaders/actions. Built on Vite. Portable. | Many releases and API churn. Assistants mix up v6/v7/v8 and Remix APIs. | 7.5 |
| TanStack Start | 1.168.58 | 15.1k (router repo) | 12.7M* | MIT | Type-safe routing, server functions, Vite-based, portable. | Its own docs still say **"Release Candidate"**. Assistants know it less well. | 6.5 |
| SvelteKit | 2.70.3 | 20.8k | 1.9M | MIT | Small bundles, nice DX. | Leaves the React ecosystem (grids, shadcn, AI UI kits). Assistants are less fluent. | 5 |
| Nuxt | 4.5.2 | 60.9k | 1.6M | MIT | Mature Vue full-stack framework. | Vue. Same ecosystem cost as SvelteKit. | 5 |
| Astro | 7.3.4 | 62.8k | 4.2M | MIT | Best for content and marketing sites. | Wrong tool for a SPA-heavy dashboard. | 3 (dashboard) / 9 (marketing site) |

\*The TanStack Start download count looks inflated by transitive or CI installs. [UNVERIFIED interpretation]

**Recommendation: Vite 8 + React 19 SPA, using TanStack Router** (or React Router 8 in SPA/data mode).
- Set it up as one pnpm monorepo with `apps/dashboard`, `apps/floor-pwa` and `packages/ui`, `packages/api-client`, `packages/i18n`.
- Both apps deploy as static files to Cloudflare Pages, Netlify, S3+CloudFront or nginx, so you're not tied to Vercel.

**Runner-up: Next.js 16.** Pick it if you want the frontend to also be your BFF (hiding Anthropic keys, proxying the API) and you value assistant fluency above everything. Build the marketing site separately in Astro.

## 2. UI component system

| Option | Latest | Stars | Weekly dl | License / cost | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **shadcn/ui (Radix or Base UI) + Tailwind v4** | shadcn CLI 4.21.0 | 124.5k | 6.7M CLI; Radix dialog 53M; @base-ui/react 9.8M | MIT, free | You own the code. Assistants are most fluent in it (v0 and others generate it). Has a data-table recipe (TanStack Table) and a charts recipe (Recharts). | You maintain the copied components. Few complex widgets built in (date-range pickers, etc. are community add-ons). | **9.5** |
| Mantine | 9.6.2 | 31.8k | 1.7M | MIT, free | Batteries included: dates, notifications, spotlight, forms, charts (Recharts wrapper). Big-button touch UI is easy. | Its own styling system. Assistants are a bit less fluent than with shadcn. Watch for v9 API drift. | 8.5 |
| MUI (Material) | 9.4.0 | 99.1k | 7.4M | MIT core; MUI X paid | Very mature, huge ecosystem. | Material look. Heavier. The best grid features are paid. | 7 |
| Ant Design | 6.6.5 | 99.6k | 2.9M | MIT | Very complete enterprise widgets (tables, forms, trees). | Distinctive look. Large bundle. | 7 |
| Chakra v3 | 3.37.0 | 40.7k | 1.2M | MIT | Good DX. | The v2 to v3 rewrite confuses assistants. Fewer data-heavy widgets. | 6 |
| HeroUI (ex-NextUI) | 3.2.6 | 30.8k | 0.48M | MIT | Polished visuals. | Consumer-app look. Thin on data widgets. | 5.5 |
| Tremor | @tremor/react 3.18.7 (**last npm release 2025-01-13**, last repo push 2025-10-10) | 3.6k | 0.29M | Apache-2.0 | Dashboard KPI and chart blocks, copy-paste model. | Effectively stagnant. The team reportedly joined Vercel. [UNVERIFIED: Vercel acquisition, Jan 2025] | 4 |
| Refine | @refinedev/core 5.0.12 | 35.7k | 0.15M | MIT (paid enterprise tier [UNVERIFIED]) | Headless CRUD, auth and access-control scaffolding. Works with shadcn/Mantine/AntD. | An extra abstraction layer. Your screens (queues, scanning, editor) are custom, not CRUD. | 5.5 |
| React Admin | 5.15.3 | 26.9k | 0.12M | MIT (paid EE modules [UNVERIFIED]) | Fast CRUD admin panels. | MUI-based and opinionated. Poor fit for custom workflows. | 4.5 |

**Recommendation: shadcn/ui on Radix** (or Base UI, which shadcn now supports [UNVERIFIED exact CLI flag]) **+ Tailwind v4.** Use one shared `packages/ui`. For the floor app, add a "large" size variant: buttons of 64px or more, 20–24px type.

**Runner-up: Mantine 9.** Choose it if you'd rather get dates, notifications and modals ready-made than own the component code.

## 3. Data grid

| Option | Latest | Stars | Weekly dl | Cost | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **TanStack Table + TanStack Virtual** | table **9.2.4** / virtual 3.14.13 | 28.4k | 14.8M / 16.9M | MIT, free | Headless and matches shadcn exactly. Server-side sort/filter/paging. Row selection for bulk actions. Assistants know it well (v8). | You build column resize, pinning and virtualization yourself. **v9 is new**: check the migration notes, because assistants write v8 code. | **9** |
| AG Grid Community | 36.2.0 | 15.6k | 2.3M | MIT, free | Virtualization, sort/filter, selection, CSV export and editing out of the box. Handles 100k rows easily. | Its own theming (Theming API) to match shadcn. Big bundle. | 8.5 |
| AG Grid Enterprise | same | — | — | **$999/developer**, perpetual with 1 year of updates. Charts Enterprise $499; bundle $1,498. | Row grouping, pivot, set filters, server-side row model, Excel/PDF export, undo/redo. | Cost. Renewal needed for updates. | 7 (only if you need grouping or Excel) |
| MUI X Data Grid | 9.14.0 (Community 2.1M dl, Pro 0.95M dl) | 5.9k | — | Pro **$299/dev/yr**, Premium **$599/dev/yr** (perpetual option available) | Polished. Pro adds pinning, multi-filter and reordering. Premium adds grouping, aggregation, Excel export and pivoting. [UNVERIFIED: exact tier split; the pricing page summary was garbled] | Only really sensible if you use MUI. | 6 |
| Glide Data Grid | 6.0.3 (**last npm release Feb 2024**) | 5.3k | 0.24M | MIT | Canvas rendering, millions of rows, very fast. | Slow maintenance. Canvas cells are harder to style and to fill with rich React content (image thumbnails, buttons). | 5 |
| Handsontable | 18.1.1 | 22.0k | 0.21M | Standard **$999/dev/yr**, Priority $1,299/dev/yr; free only for non-commercial use | Spreadsheet-style editing. | Wrong shape for order queues. Pricey. | 3 |

**Recommendation: TanStack Table + Virtual** (the shadcn data-table pattern), with server-side paging, filtering and sorting through TanStack Query. "Thousands of rows" is easy with virtualization.

**Runner-up: AG Grid Community (free).** Upgrade to Enterprise ($999 one-time) only if owners demand Excel export, grouping or pivots.

## 4. Data fetching, state and forms

| Option | Latest | Stars | Weekly dl | Role | Fit |
|---|---|---|---|---|---|
| **TanStack Query** | 5.103.2 | 50.4k | 48.0M | Server cache, mutations, optimistic bulk actions. Its persister and `onlineManager` help offline. | **9.5** |
| SWR | 2.5.1 | 32.5k | 12.1M | Simpler, but weaker mutations and offline support. | 6.5 |
| **Zustand** | 5.0.15 | 58.7k | 39.8M | Small client and UI state (selected rows, scan session, printer). | **9** |
| Jotai | **3.0.0** | 21.3k | 4.2M | Atomic state. Fine, but v3 is new. | 7 |
| Redux Toolkit (+RTK Query) | 2.12.0 | 11.2k | 21.6M | More ceremony than a solo dev needs. | 5.5 |
| **react-hook-form + zod** | 7.88.0 | 44.9k | 42.4M | Most assistant-familiar. Works with shadcn `<Form>`. | **9** |
| TanStack Form | 1.33.5 | 6.7k | 2.1M | Stronger typing. Growing, but assistants know it less. | 7.5 |
| Conform | 1.21.1 | 2.6k | 0.17M | Built for server actions and progressive enhancement. Pointless in a SPA. | 4 |

**Picks:** TanStack Query + Zustand, and react-hook-form + zod for forms.

**Runner-ups:** SWR (or plain Query) + Jotai for state, and TanStack Form for forms.

## 5. Charts

| Option | Latest | Stars | Weekly dl | License | Notes | Fit |
|---|---|---|---|---|---|---|
| **Recharts (via shadcn charts)** | 3.10.1 | 27.6k | 42.5M | MIT | SVG. Assistants know it very well. Plenty for KPIs, throughput and sales trends. | **9** |
| ECharts (echarts-for-react) | 6.1.0 | 67.4k | 3.7M | Apache-2.0 | Canvas, handles large series, heatmaps, zoom. | 8 |
| AG Charts Community | 14.2.0 | — | 1.3M | MIT (Enterprise $499/dev) | Pairs well with AG Grid. | 6.5 |
| Chart.js | 4.5.1 | 67.7k | 9.0M | MIT | Simple canvas charts. The React wrapper is thin. | 6.5 |
| Visx | 4.0.0 | 21.1k | 3.7M | MIT | Low-level D3 primitives. Lots of work. | 5 |
| Nivo | 0.99.0 | 14.1k | 1.1M | MIT | Pretty, but heavy and still pre-1.0. | 6 |
| Tremor | see §2 | — | — | Apache-2.0 | Stagnant. | 4 |

**Recommendation: Recharts (shadcn chart components).** **Runner-up: ECharts**, for dense time series or heatmaps such as per-printer utilization.

## 6. Image viewing and design editing

| Option | Latest | Stars | Weekly dl | Cost | Use | Fit |
|---|---|---|---|---|---|---|
| **OpenSeadragon** | 6.1.1 (published 2026-09-09) | 3.5k | 83k | BSD-3, free | Gang-sheet viewer. Deep-zoom tiles (DZI/IIIF) generated server-side with libvips `vips dzsave` or sharp `.tile()`. Smooth pan and zoom on very tall sheets. | **9.5** (viewer) |
| **Konva + react-konva** | 10.7.0 / 19.3.0 | 14.8k | 1.9M / 1.5M | MIT, free | Custom listing and design editor: layers, transform handles, text, snapping. Declarative React API that assistants handle well. | **8.5** (editor) |
| Fabric.js | 7.4.0 | 31.5k | 0.71M | MIT | Richer built-ins (text editing, SVG import/export, filters). Imperative API. | 8 |
| PixiJS | 8.21.0 | 48.2k | 0.80M | MIT | WebGL renderer, but no editor tooling. Overkill. | 4 |
| Polotno SDK | 4.13.0 | — | 21k | **Grass Roots $249/mo ($2,490/yr)**; Self-Serve $899/mo ($9,990/yr); Enterprise custom; 60-day dev trial | Canva-like template editor in days, plus server rendering. | 7 (if a customer-facing personalization editor is core) |
| IMG.LY CE.SDK | 1.82.1 | — | 54k | **Quote only**, no public prices; 30-day trial | Most polished print-ready editor. | 5 (cost unknown, likely high [UNVERIFIED]) |

**Recommendations:**
- Viewer: **OpenSeadragon** with server-side tiles.
- Editor: **Konva/react-konva**.
- **Runner-up editor: Fabric.js.** Buy **Polotno Grass Roots ($249/mo)** only if shop customers need self-serve template personalization.

**Hard constraint:** DTF print-resolution files (for example 22" × 200"+ at 300 DPI, roughly 6,600 × 60,000+ px) exceed browser canvas limits (about 16k px per side / about 268M px area in Chromium, lower on iOS [UNVERIFIED exact limits]). Edit on low-resolution proxies and render final output server-side with sharp or libvips.

## 7. PWA, offline and scanning

| Option | Latest | Stars | Weekly dl | Cost | Notes | Fit |
|---|---|---|---|---|---|---|
| **vite-plugin-pwa (Workbox)** | 1.3.0 (last repo push 2026-05) | 4.3k (Workbox 13.0k) | 3.4M | MIT | Manifest and precaching with zero config. | **9** |
| Serwist (@serwist/next) | 9.5.12 | 1.5k | 0.30M | MIT | Only if you use Next.js. | 7 (Next) |
| **Dexie.js** | 4.4.6 | 14.6k | 1.7M | Apache-2.0 (Dexie Cloud is a paid add-on) | IndexedDB outbox for queued scans. `useLiveQuery` for React. | **9.5** |
| onscan.js | 1.5.2 (**last release 2020-05**) | 338 | 40k | MIT | Keyboard-wedge detection. Unmaintained. | 5 |
| **Custom wedge hook (~50 LOC)** | — | — | — | free | Buffer keydown events. Treat it as a scan if keys arrive less than ~30 ms apart and end with Enter. Program the scanners with a prefix/suffix and ignore key repeats. | **9** |
| **barcode-detector** (polyfill for the native BarcodeDetector API, backed by zxing-cpp WASM) | 3.2.2 | — | 1.4M | MIT | Camera fallback. Uses the native API on Android Chrome. | **8.5** |
| @zxing/browser / library | 0.2.1 (published 2026-07) / — | 2.9k | 0.79M / 1.2M | MIT/Apache | Alternative camera decoder. | 7.5 |
| html5-qrcode | 2.3.8 (**last release 2023-04**) | 6.2k | 1.05M | Apache-2.0 | Stale. | 4 |
| STRICH | — | — | — | **Basic €99/mo** (10k scans), Professional €249/mo (100k), Business from €4,000/yr per app | Fast, reliable camera scanning of 1D codes. | 7 (only if camera becomes primary) |
| Scandit | — | — | — | Quote only | Enterprise-grade, expensive. | 3 |

**Recommendation:** vite-plugin-pwa + Dexie outbox, a custom keyboard-wedge hook (use onscan.js as reference), and the barcode-detector polyfill for camera fallback.

How the offline outbox should work:
- Give each scan a client-generated UUID so replays are safe (the server de-duplicates by key).
- Flush the queue on the `online` event, on an interval and on app focus.
- Don't rely on the Background Sync API; it is Chromium-only.

Other floor-app details:
- Use the Screen Wake Lock API to keep screens on.
- Play pre-decoded Web Audio buffers for success/error sounds.
- Lock orientation to landscape via the manifest.

**Runner-up:** STRICH Basic (€99/mo) if camera scanning turns out unreliable.

Use Android or Chromebook tablets with Chrome in kiosk mode rather than iPads, for better PWA and API support. [UNVERIFIED as a blanket claim; test your scanners]

## 8. AI chat UI

| Option | Latest | Stars | Weekly dl | License | Notes | Fit |
|---|---|---|---|---|---|---|
| **Vercel AI SDK (`ai` + `@ai-sdk/react` + `@ai-sdk/anthropic`)** | ai **7.0.113** / react 4.0.116 | 26.9k | 17.9M / 5.8M | Apache-2.0 | `useChat` streaming, tool calls and generative UI. Framework-agnostic: the server can be any Node/Hono/Express endpoint, no Vercel needed. First-class Anthropic provider. | **9.5** |
| **assistant-ui** | 0.15.21 | 12.3k | 1.3M | MIT | Ready-made shadcn-style chat components (threads, attachments, tool UIs) on top of the AI SDK runtime. Still pre-1.0. | **8.5** (complement) |
| CopilotKit | 1.73.3 | 37.5k | n/a (API rate-limited) | MIT (paid cloud tiers [UNVERIFIED]) | In-app copilot that reads app state and runs actions. Heavier and more opinionated. | 6.5 |

**Recommendation:** AI SDK for transport and hooks, with assistant-ui for the chat components. **Runner-up:** AI SDK with hand-built shadcn components, or Vercel's AI Elements [UNVERIFIED current status].

## 9. i18n (English + Spanish)

| Option | Latest | Stars | Weekly dl | Notes | Fit |
|---|---|---|---|---|---|
| **react-i18next** | 17.0.15 | 10.0k | 11.7M | Framework-agnostic and the most assistant-familiar. Namespaces, lazy-loaded JSON, ICU plugin. | **9** |
| Lingui | @lingui/core 6.8.0 | 5.9k | n/a (API rate-limited) | Compile-time message extraction and small runtime. Macro setup is less familiar to assistants. | 8 |
| next-intl | 4.14.6 | 4.4k | 4.1M | Excellent, but Next.js only. | 9 if Next / 0 otherwise |

**Recommendation:** react-i18next, with a shared `packages/i18n` and per-user language saved on the staff profile. **Runner-up:** Lingui (or next-intl if you go with Next.js).

## 10. Dev tooling

| Item | Facts | Pick |
|---|---|---|
| GitHub vs GitLab | GitHub Free includes **2,000 Actions minutes/month** for private repos; Pro includes 3,000. Linux 2-core costs **$0.006/min** beyond that. Self-hosted runners and public repos are free. GitLab Free has about 400 CI min/month [UNVERIFIED]. GitHub Pro costs $4/mo [UNVERIFIED]. | **GitHub** (ecosystem and AI tool integrations). A solo monorepo with Turbo cache should fit in 2,000 min/month, so **$0**. |
| Dependabot vs Renovate | Both free. Renovate: 22.6k stars, groups and auto-merges minor/patch updates, handles monorepos well. | **Renovate** (grouped weekly PRs, less noise). Runner-up: Dependabot with `groups:`. |
| Storybook vs Ladle | Storybook 10.6.0, 91.1k stars, 15.5M dl. Ladle 5.1.1, 3.0k stars, last push 2026-06. | Skip both at first (the shadcn source is the catalog). If needed, **Storybook** (assistants know it, has testing addons). Ladle is the lighter runner-up. |
| AI code review | CodeRabbit: Essentials **$24/dev/mo** (annual), Team $48, Advanced $72, 14-day trial. Alternatives: Claude Code GitHub Action (pay per API use) and GitHub Copilot code review (inside Copilot plans [UNVERIFIED pricing]). | **CodeRabbit Essentials ($24/mo)**, optional. Runner-up: the Claude Code Action, paid per use. |
| Linear vs GitHub Projects | Linear Free: unlimited members, 2 teams, **250 issues cap**. Basic $10/user/mo, Business $16. GitHub Projects is free and linked to PRs. | **GitHub Issues + Projects** ($0). Runner-up: Linear Free until you hit 250 issues. |

---

## Recommended stack summary

**Recommended picks:**
- Vite 8 + React 19 SPA with TanStack Router, in a pnpm monorepo with two apps.
- shadcn/ui + Tailwind v4.
- TanStack Table + Virtual.
- TanStack Query + Zustand.
- react-hook-form + zod.
- Recharts (shadcn charts).
- OpenSeadragon for the viewer; Konva for the editor.
- vite-plugin-pwa + Dexie, a custom wedge hook and barcode-detector.
- AI SDK 7 + @ai-sdk/anthropic + assistant-ui.
- react-i18next.
- GitHub + Actions + Renovate + GitHub Projects.

**Runner-ups:**
- Next.js 16 instead of the Vite SPA.
- Mantine instead of shadcn/ui.
- AG Grid Community instead of TanStack Table.
- ECharts instead of Recharts.
- Fabric.js instead of Konva.
- STRICH for camera scanning.
- Lingui instead of react-i18next.
- Dependabot instead of Renovate.
- Linear Free instead of GitHub Projects.

## Paid-license cost per month

| Item | Recommended? | Cost |
|---|---|---|
| All core libraries above | Yes | **$0** (MIT/Apache/BSD) |
| GitHub Free + Actions (within 2,000 min) | Yes | **$0** |
| CodeRabbit Essentials (1 developer) | Optional, recommended | **$24/mo** (annual billing) |
| **Total for recommended picks** | | **$0–24/mo** |
| *Add-ons only if needed:* AG Grid Enterprise | No | $999 one-time (about $83/mo over 1 year of updates) |
| STRICH Basic | No | €99/mo |
| Polotno Grass Roots | No | $249/mo |
| MUI X Pro / Premium | No | $299 / $599 per developer per year |
| IMG.LY / Scandit | No | Quote only |

## Main risks and caveats
1. **Major-version drift.** Many packages just moved to a new major. Pin versions and tell your coding assistant which ones you use (TanStack Table 9, React Router 8, AI SDK 7, Jotai 3, Vite 8).
2. **TanStack Start is still an RC** according to its own docs. I only suggest TanStack Router, not Start.
3. **Canvas size limits.** You can't edit gang sheets at full resolution in the browser; you need server-side tiling and rendering.
4. **Stale scanner libraries.** onscan.js, html5-qrcode and Glide Data Grid have had no npm release in 1.5–6 years.
5. **Unverified items.** Tremor's acquisition by Vercel, the exact MUI X tier features, GitLab CI minutes, GitHub Pro and Copilot pricing, and browser canvas limits were not checked here.

## Sources
- [AG Grid pricing](https://www.ag-grid.com/license-pricing/)
- [MUI pricing](https://mui.com/pricing/)
- [Handsontable pricing](https://handsontable.com/pricing)
- [Polotno SDK pricing](https://polotno.com/sdk/pricing)
- [IMG.LY pricing](https://img.ly/pricing)
- [STRICH](https://strich.io/#pricing)
- [Scandit pricing](https://www.scandit.com/pricing/)
- [CodeRabbit pricing](https://www.coderabbit.ai/pricing)
- [Linear pricing](https://linear.app/pricing)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Next.js deploying docs](https://nextjs.org/docs/app/getting-started/deploying)
- [TanStack Start overview](https://tanstack.com/start/latest/docs/framework/react/overview)
- [Tremor repo](https://github.com/tremorlabs/tremor)
- npm registry (registry.npmjs.org), npm downloads API (api.npmjs.org), GitHub REST API (api.github.com/repos/*)

