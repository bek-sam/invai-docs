# Glossary

Every term, once, in plain words, with where it shows up in InvAI. Grows as new modules
are written; right now it covers modules 01–02. Add a term the first time a lesson uses
it — don't duplicate an entry that's already here.

## The business
- **DTF (direct-to-film)** — a t-shirt printing method: a design is printed onto film,
  then heat-pressed onto a blank shirt. The whole platform is built around this
  workflow. See `01-big-picture/01-the-dtf-business.md`.
- **Blank** — a plain, undecorated shirt bought wholesale (brands like Gildan, Bella+Canvas,
  Comfort Colors). Stock is tracked per blank variant, not per listing.
- **Gang sheet** — one large sheet of film with many designs nested onto it, to save
  film and press time. Built by the Gang Sheet Builder module.
- **SKU (stock-keeping unit)** — the code a marketplace uses to identify a listing
  variant; shops often encode design + style + color + size into it. InvAI's SKU mapper
  turns that code into a design/blank/color/size the system understands.
- **Marketplace / channel** — a sales platform (Etsy, Amazon, Shopify, TikTok Shop,
  Walmart) where a shop lists and sells products.
- **Ship-by date** — the real deadline a marketplace sets for dispatching an order; used
  to sort the Order Hub, as opposed to the order's placed date.
- **Personalization** — a buyer-supplied custom detail (name, date, photo) that must be
  rendered into print-ready artwork before a gang sheet is built.
- **Trademark-risk check** — an automated check (not legal advice) that flags a listing
  likely to infringe a trademark before it's published.
- **Golden path** — the one critical order → gang sheet → press → ship → profit sequence
  that must always work end to end; InvAI's main E2E test is named for it.
- **One order item = one physical unit** — InvAI's core modeling rule: a quantity-3
  order line becomes 3 separate `order_items` rows, each independently trackable (its
  own state, scans, reprints).
- **Scope (`scope.md`)** — the product-manager-owned document listing exactly what's
  MVP-in, MVP-out, and deferred-with-a-trigger. Nothing outside it gets built without a
  scope-change request.

## Repos and architecture
- **Repo (repository)** — one independent git project. InvAI has 8, side by side on
  disk, each pushed straight to its own `main` branch (no feature branches or PRs).
- **Monorepo** — a single repository holding multiple apps/packages, usually built
  together by a workspace tool. InvAI deliberately does *not* use this
  (`decisions/0001-keep-multi-repo.md`).
- **`@invai/contracts`** — the shared npm package built from `invai-contracts`: every
  API procedure, schema, state and event, consumed by `invai-backend`, `invai-web` and
  `invai-floor`.
- **`@invai/ui`** — the shared component/theme/i18n-strings package built from
  `invai-ui`, consumed by `invai-web` and `invai-floor`.
- **`link:../<repo>`** — a pnpm dependency type pointing at a local folder instead of a
  published package version, used for local development across the 8 repos.
- **Worktree** — a second working copy of the same git repo on a different branch,
  usually used for isolated review/testing. Risky if it runs `pnpm install` (it can
  repoint the shared `node_modules` symlink for everyone).
- **oRPC** — the contract-first RPC framework: one TypeScript contract generates both
  the backend's implementation surface and every client's typed call signatures.
- **Procedure** — one callable contract endpoint (e.g. `orders.list`), with its required
  permission and auth mode declared as metadata on the procedure itself, not in the
  handler body.
- **Zod** — the schema/validation library used to define every procedure's input,
  output and shared data shapes in `@invai/contracts`.
- **Hono** — the lightweight HTTP framework the backend's `api` process runs on (routes,
  webhooks, SSE streaming).
- **Better Auth** — the library providing user session cookies for web logins. Floor
  (tablet) sessions use a separate station-token + PIN scheme instead.
- **RLS (Row-Level Security)** — a Postgres feature that filters every query against a
  table by a policy condition. InvAI's policy checks a transaction-local
  `app.company_id` setting, so one tenant's query can never see another tenant's rows.
- **`withTenant` / `withSystem`** — the two ways backend code opens a scoped database
  transaction. `withTenant(companyId, fn)` is for normal per-shop requests (RLS
  enforced); `withSystem(fn)` is only for the outbox relay, cross-tenant jobs and the
  seed (bypasses RLS).
- **Tenant / multi-tenancy / `company_id`** — every shop ("company") using InvAI is a
  tenant; every tenant-owned database table carries a `company_id` column and an RLS
  policy keyed on it.
- **Transactional outbox** — the pattern of writing an event row (`outbox_events`) in
  the exact same database transaction as the state change it describes, so the event
  and the change can never disagree (one can't commit without the other).
- **BullMQ** — the Redis-backed job queue library the backend's `worker` process uses to
  run background jobs, grouped into five named queues: `sync`, `render`, `ship`, `ai`,
  `reports`.
- **Valkey / Redis** — the in-memory store backing BullMQ queues, rate limits and
  pub/sub for realtime events. Valkey is an open-source Redis-compatible fork used
  locally.
- **SSE (Server-Sent Events)** — a one-way, long-lived HTTP connection a server uses to
  push events to a client without the client polling. InvAI uses it for live dashboard
  and floor updates.
- **Mock provider** — a deterministic stand-in for a real external integration (e.g.
  EasyPost, Claude, a marketplace API), automatically selected when the matching env var
  or key is absent, so the whole platform works end to end with no real credentials.
  Never removed, even once real keys exist.
- **MinIO / S3** — the object storage holding actual files (print art, gang sheets,
  labels). The backend and `invai-imaging` both read/write it directly by key; file
  bytes are never shipped through the backend's own API request/response bodies.
- **pyvips** — the Python image-processing library `invai-imaging` uses for gang-sheet
  nesting, composing and print checks.
- **FastAPI** — the Python web framework `invai-imaging`'s HTTP service is built on.

## The team (introduced here, detailed in module 10)
- **Task card** — a single unit of work with one named owner, a defined-done checklist
  and owned file paths, filed under `invai-docs/waves/<n>/`.
- **Wave** — a batch of at most 5 task cards run together (3–4 agents at once), followed
  by an integration gate and a review before the next wave starts.
- **ADR (decision record)** — a short, numbered file in `invai-docs/decisions/` recording
  one architecture/product/process decision: context, decision, consequences.
