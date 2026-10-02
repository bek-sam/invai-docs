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

## The stack (module 03)
- **Strict mode (TypeScript)** — the `tsconfig.json` setting turning on a bundle of
  stricter type checks (e.g. `string | null` must be handled, not treated as
  `string`). Every InvAI TypeScript repo has it on.
- **Standard Schema** — a shared interface several validation libraries (Zod, Valibot,
  ArkType) implement, so a tool like oRPC can accept any of them without hard-coding
  one.
- **Contract-first** — the API's shape is declared once, in a schema, before any
  handler is written; the opposite of "code-first," where types are inferred from
  function signatures.
- **`stubRouter`** — an oRPC helper that returns a 501 for any contract procedure
  without a real handler yet, so an unfinished module still type-checks and runs.
- **OpenAPI** — a standard format for describing a REST API's endpoints and shapes;
  oRPC generates one from the same contract that drives its typed RPC clients.
- **Biome** — a single Rust-based tool doing both formatting and linting for every
  TypeScript repo in InvAI, replacing a separate ESLint + Prettier pair.
- **drizzle-kit** — Drizzle's migration generator; diffs the TypeScript schema against
  its journal and writes the SQL migration files.
- **pgvector** — a Postgres extension adding a vector column type and similarity
  search; installed for future embedding-based features, not yet load-bearing.
- **`maxmemory-policy noeviction`** — a Redis/Valkey server setting that refuses to
  silently drop keys under memory pressure, required for a job queue to be reliable.
- **Presigned URL** — a time-limited, signed URL granting temporary direct access to
  one object in S3/MinIO, so a browser or service can upload/download without the
  backend proxying the bytes.
- **Object key** — the path-like string identifying one file inside a storage bucket;
  InvAI's keys encode the owning company so storage-layer checks are possible.
- **SPA (single-page app)** — a frontend that loads once and updates itself via
  JavaScript instead of requesting a new HTML page from the server on every
  navigation; both `invai-web` and `invai-floor` are built this way.
- **Headless (UI library)** — a library (like TanStack Table) that manages
  behavior/state but renders no markup of its own; the app supplies the visuals.
- **HMR (hot module replacement)** — Vite's dev-time feature that swaps changed code
  in the running browser without a full page reload.
- **MaxRects** — a rectangle-packing algorithm (via the Python `rectpack` library)
  used to nest gang-sheet designs efficiently.
- **OrbStack** — the Docker-compatible container runtime used on this project's dev
  machine, with its own known hang/recovery behavior distinct from Docker Desktop.
- **Pin by digest / pin by SHA** — referencing an exact, immutable image or commit (a
  cryptographic hash) instead of a mutable tag, so what runs in CI can't silently
  change underneath you.
- **SST (v3)** — infrastructure-as-code written in TypeScript, with pre-built
  components for common AWS resources; used for InvAI's (not yet deployed) AWS setup.

## Data and tenancy (module 04)
- **Migration** — a versioned SQL script, generated from the Drizzle schema, that
  changes the database; applied in order and never hand-edited after the fact.
- **Journal** (`meta/_journal.json`) — drizzle-kit's ordered record of every migration
  it has generated.
- **Expand/contract migration** — splitting a risky schema change into a safe "add the
  new thing without fully validating it yet" step and a later "finish validating it"
  step, to avoid locking a busy table for a long scan.
- **`NOT VALID` / `VALIDATE CONSTRAINT`** — a Postgres feature letting a new
  constraint be added instantly (skipping the check on existing rows) and validated
  separately later, with only a brief lock.
- **`set_config(key, value, true)`** — the Postgres function `withTenant`/
  `withSystem` use to set a transaction-local session variable, so it can never leak
  across pooled connections or requests.
- **Composite foreign key** — a foreign key spanning two columns (`company_id, id`)
  instead of one, so the database itself enforces that a child row's tenant matches
  its parent's; a plain single-column FK ignores RLS and is a real leak vector.
- **`tenantKey`** — the Drizzle helper adding the `(company_id, id)` unique constraint
  a composite foreign key points at.
- **Structural test vs. behavioral test** — a structural test checks that the right
  configuration exists (RLS enabled, a composite FK declared); a behavioral test
  actually performs the blocked action and checks it fails.
- **Vendor scope (`withVendor`)** — a second, narrower cross-tenant access pattern for
  the DTF vendor portal, using its own policy type rather than the normal tenant
  policy.
- **Integer cents** — storing a money amount as a whole number counting cents (1230
  for $12.30), with no floating-point fractional part to round or drift.
- **`*Pct` field** — a percentage stored as a plain number matching how a person would
  say it (6.5 for "6.5%"), distinct from a 0..1 ratio field.
- **Ratio (0..1)** — a fraction-of-a-whole number (0.87 for "87% utilized"), used
  where the value is a true proportion rather than a percentage of a price.
- **`ITEM_TRANSITIONS`** — the shared table (in `@invai/contracts`) defining which
  `order_items` states can move to which other states; one source read by both the
  backend's enforcement code and every frontend's UI logic.
- **State machine (order item)** — the twelve `ORDER_ITEM_STATES` an individual order
  item moves through from import to delivery, each unit tracked independently of its
  siblings on the same order line.

## Core flows (module 05)
- **Normalized order** — a marketplace order after a channel adapter has translated it
  out of that marketplace's own format, into the one shape `importNormalizedOrders`
  understands.
- **SKU mapping rule** — a per-shop configured pattern that extracts design/style/
  color/size fields out of a raw channel SKU string.
- **Needs-mapping state** — the `order_item.state` value meaning "this unit's SKU
  didn't resolve yet"; blocks the item from nesting until resolved.
- **SKU map inbox** — the office-facing screen/query surfacing every unmapped SKU,
  grouped by channel, with counts and sample titles.
- **Nesting** — packing multiple designs onto one gang sheet as efficiently as
  possible, reserving space for each design's QR label strip.
- **Compose** — the step that renders the actual gang-sheet image (PNG/PDF), as
  opposed to just computing the nested layout.
- **Transfer** — the physical, cut piece of printed film for one unit, carrying its
  own QR code; what the production floor scans at press time.
- **Two-scan check** — the press station's pattern of scanning the transfer first,
  then the blank/tote, before the server renders a match/mismatch verdict.
- **Mismatch reason** — a specific, named reason a floor scan was blocked (wrong
  style, color, size, design or order), chosen so the on-screen message tells the
  presser exactly what to fix.
- **Dexie** — a JavaScript wrapper around the browser's IndexedDB; backs
  `invai-floor`'s offline scan queue.
- **Idempotency key / `clientScanId`** — a stable identifier on a scan command, so a
  replayed (or offline-queued) submission is recognized as the same scan rather than a
  new one.
- **Idempotent side effect** — an outward action (buying a label, pushing tracking)
  made safe to retry by committing an intent before the call and reading back for an
  existing result before retrying.
- **Carrier adapter** — the interface a real shipping provider (EasyPost) and its
  mock both implement, so the rest of the codebase calls one shape regardless of
  which is active.
- **Buckets (profit)** — the named cost/revenue categories (`revenue`, `blankCost`,
  `transferCost`, `labelCost`, …) every order's profit is broken into.
- **Largest-remainder allocation** — a way to split one amount across several parts so
  the parts always sum exactly back to the original, with no cent lost or invented to
  rounding.
- **Stuck intent** — a shipment left in `"buying"`/`"voiding"` status longer than
  expected, usually from an interrupted buy call; recovered by a sweep job rather than
  left for a human to notice.

## The team (introduced here, detailed in module 10)
- **Task card** — a single unit of work with one named owner, a defined-done checklist
  and owned file paths, filed under `invai-docs/waves/<n>/`.
- **Wave** — a batch of at most 5 task cards run together (3–4 agents at once), followed
  by an integration gate and a review before the next wave starts.
- **ADR (decision record)** — a short, numbered file in `invai-docs/decisions/` recording
  one architecture/product/process decision: context, decision, consequences.
