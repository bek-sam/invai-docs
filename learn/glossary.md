# Glossary

Every term, once, in plain words, with where it shows up in InvAI. Grows as new modules
are written; right now it covers modules 01–13. Add a term the first time a lesson uses
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

## Reliability (module 06)
- **Transactional outbox** — writing an event row in the exact same database
  transaction as the state change it describes, so the event and the change can
  never disagree; InvAI's relay (`src/worker/outbox-relay.ts`) turns committed rows
  into jobs.
- **Relay** — the background loop polling `outbox_events` for undispatched rows and
  enqueueing the BullMQ jobs subscribed to each event name.
- **Commit the intent** — writing "I'm about to do this" to the database *before*
  calling an external, hard-to-undo API, so a crash mid-call leaves evidence instead
  of silence (buying a label, pushing tracking).
- **Read-back before retry** — checking whether an external effect already happened
  before asking a provider to do it again, instead of assuming a retry is safe by
  default.
- **Backoff** — the growing delay between a job's retry attempts after a failure.
- **Jitter** — randomizing a retry delay within a range, so many jobs that failed
  together don't all retry at the exact same instant and re-hit a struggling provider
  in lockstep.
- **Stalled job** — a BullMQ job whose worker appears to have died or frozen (its
  lock expired without being renewed in time); put back in the queue to run once more
  before failing for good.
- **Dead-letter queue (DLQ)** — where a job lands after a permanent failure or
  repeated stalling; InvAI's is listable and redrivable at `/internal/dlq`.
- **Permanent vs. transient failure** — a permanent failure (bad input, revoked
  token) fails a job immediately with no retries (`permanentFailure()`); a transient
  one (5xx, timeout, 429) retries with backoff, because waiting might actually help.
- **Fail open / fail closed** — what a safety check does when it can't be evaluated
  (e.g. Redis is down). InvAI's rate limiters and spend breaker fail open (allow the
  request, log and alert) rather than fail closed (block everyone), because an
  infrastructure blip shouldn't become a platform-wide outage.
- **Token bucket** — a rate-limiting scheme with a burst capacity that refills
  continuously over time, used for InvAI's per-company API rate limits.
- **Adapter** — the shared interface a real integration and its mock both implement
  (`CarrierAdapter`, `ChannelAdapter`, `BillingProvider`, `AiProvider`), so calling
  code never branches on which one answered.
- **Sample / demo workspace** — a tenant flagged (`tenancy.demo`) as a demo, forced
  onto every mock provider regardless of what real keys the environment has, so it
  can never spend real money or send real data out.
- **`ALLOW_MOCKS`** — a production-only escape hatch letting a demo/staging
  deployment boot on mock providers even in a "production" environment.

## AI features (module 07)
- **Gateway (AI)** — the one module (`src/ai/gateway.ts`) every AI model call passes
  through, so provider choice, PII scrubbing, cost metering and schema validation are
  enforced in exactly one place, not reinvented per feature.
- **Provider (AI)** — one AI vendor's implementation of the shared `AiProvider`
  interface (Anthropic, OpenAI, or the mock).
- **Structured output** — a model's answer constrained to match a specific schema
  (a Zod schema, in InvAI's case), rather than free-form text the caller parses by
  hand.
- **Prompt (InvAI sense)** — a versioned `PromptDef` object: a stable `system` prefix,
  a `user` renderer for the varying part, and a Zod output schema.
- **Prompt caching** — a provider pricing a reused, identical prefix of a prompt far
  cheaper than fresh tokens; why InvAI's prompts put stable text first and variable
  content last.
- **Prompt injection** — an attack where text meant to be *data* (a buyer's message,
  an imported listing) is crafted to look like an instruction, trying to redirect the
  model; defended against with `DATA_RULE` and `dataBlock()`.
- **Refusal** — a model declining to answer; the gateway turns this into a specific,
  named error (`AiRefusalError`) instead of passing through empty or ambiguous output.
- **Validator (AI)** — deterministic code checking a model's already schema-valid
  answer against InvAI's own hard business rules (e.g. a channel's title-length
  limit), separate from and in addition to the schema check.
- **Credit ledger** — the per-shop, per-billing-period record of AI usage against a
  plan's allowance; the primary limit on how much AI a shop can use.
- **Spend breaker** — the platform-wide and per-tenant daily dollar caps sitting on
  top of the credit ledger as a backstop against a runaway loop or a leaked key.
- **Reasoning effort** — a per-call setting (`low`/`medium`/`high`, or none) trading
  more "thinking" for quality against more tokens (and cost) per call.
- **Eval (evaluation set)** — a fixed list of known-answer cases (`cases.jsonl`), run
  through the real gateway, used to measure an AI route's quality with real numbers
  instead of a feeling.
- **Plumbing vs. quality (eval sense)** — plumbing is "did the system wire this
  correctly" (schema-valid, right cardinality), checkable even against the mock;
  quality is "did the model get the right answer," checkable only with a real
  provider.
- **Baseline (eval sense)** — the frozen last-measured eval result
  (`evals/baseline.json`), compared against to catch a quality regression.
- **pg_trgm** — a Postgres extension providing trigram-based fuzzy text similarity,
  used to find candidate trademark matches before any AI call.
- **Tool (assistant)** — a named, typed, read-only function the chat assistant can
  call, each scoped to one tenant and described precisely enough to use correctly.

## Quality (module 08)
- **Unit test** — a test of a pure function's logic in isolation, no database, no
  network, no tenant context.
- **Acceptance test (InvAI sense)** — a Vitest test against a real `invai_test`
  database, through real tenant fixtures, proving one specific Given/When/Then
  criterion from a task card; owned by QA, read-only for the implementer.
- **E2E (end-to-end) test** — a Playwright test driving a real flow across the whole
  stack, proving the layers actually connect, not just that each one works alone.
- **Red first** — writing a test before the behavior exists and confirming it fails
  for the right reason, so passing later is actual proof the behavior was built.
- **Held-back case** — a test case QA keeps out of the implementer's view until after
  they report a card done, specifically to check coverage beyond what was visible.
- **Fixture** — a reusable helper (`createCompany`, `createOrder`, ...) that builds a
  realistic starting state for a test without each test reinventing that setup.
- **Integration gate** — the wave-end checkpoint where every repo's own checks plus
  the full E2E suites run together, on a fresh seed, before anything is pushed.
- **CI (continuous integration)** — automated checks (lint, typecheck, test, build)
  running on every push, independent of and faster than a full integration gate.
- **Smoke test** — a shallow check that something basic works (a screen loads with no
  console errors), as opposed to a deep check of correct behavior.
- **Independent review** — a different agent, given only the card/diff/report (never
  the author's reasoning), re-running checks and exercising behavior before a card
  can be pushed.
- **Co-reviewer** — an additional reviewer required only for a card's specific risk
  flags (contract change, migration, tenancy/PII/auth, prompts, new UI).
- **Weakened test** — a test changed so it no longer actually checks the behavior it
  claims to, without an equal or stronger check added elsewhere.
- **Verdict (review)** — a review's final decision: `approve`, `changes-required`, or
  `escalate`, each with specific, named conditions.
- **Fail-without-change check** — running a new or changed test against the code
  *before* the fix, to prove it would have caught the problem the fix addresses.

## The team (introduced here, detailed in module 10)
- **Task card** — a single unit of work with one named owner, a defined-done checklist
  and owned file paths, filed under `invai-docs/waves/<n>/`.
- **Wave** — a batch of at most 5 task cards run together (3–4 agents at once), followed
  by an integration gate and a review before the next wave starts.
- **ADR (decision record)** — a short, numbered file in `invai-docs/decisions/` recording
  one architecture/product/process decision: context, decision, consequences.

## Security (module 09)
- **Station token** — a long random secret (`st1.<companyId>.<random>`) issued once to one
  physical floor tablet, stored only as its SHA-256 hash, proving "this is a known device
  for this shop."
- **Floor session** — the signed, time-limited token (`fs1.<payload>.<sig>`) issued after
  a station token *and* the right staff PIN are both presented.
- **`auth` mode** — a contract procedure's declared login requirement: `"user"` (web
  session), `"floor"` (floor session), `"station"` (bare station token only), or
  `"public"`.
- **`disabledPaths`** — a Better Auth config option that removes an HTTP route entirely;
  used to turn off organization-management endpoints InvAI's own code replaces.
- **Email-verified procedure** — one of a small, explicit set of procedures (money-moving
  ones) that require a verified email on top of the normal permission check.
- **AES-256-GCM** — an authenticated encryption cipher: it both hides data and lets the
  decrypting side detect if the ciphertext was tampered with; used for buyer PII and
  channel credentials.
- **Key ring** — a list of encryption keys where one is "primary" (used for new
  encryption) and all are valid for decryption, enabling key rotation without a mass
  re-encryption migration.
- **Unkeyed vs. keyed hash** — `sha256Hex` (no secret, safe only for long random inputs
  like tokens) versus `hmacHex` (uses a server secret, safe for anything, including
  guessable values like a dollar amount or an email subject).
- **DSAR (data-subject access request)** — a legal request (GDPR/CCPA) from a real person
  asking what data is held about them, or asking for it to be deleted or exported.
- **Retention window** — a fixed time limit after which data must be deleted, enforced by
  a scheduled job rather than left to manual cleanup.
- **Webhook verification** — checking a cryptographic signature on the *raw* request body
  to prove a webhook really came from the marketplace it claims to be from.
- **Delivery id** — a unique identifier a marketplace attaches to one specific webhook
  send, used to detect and ignore a resend of the same event.
- **Unique partial index** — a Postgres index that enforces uniqueness only among rows
  matching a condition, letting multiple `pending` attempts exist while blocking two real
  connections to the same store.
- **Findings log** — `invai-docs/security/v1-review.md`: one table of every known security
  issue, its severity, and a status that names the fix's commit and the test that proves
  it, kept current rather than archived once "done."
- **Compliance webhook** — a Shopify-specific webhook topic (`customers/redact`,
  `shop/redact`, ...) tied to a legal data-handling obligation, handled inline rather than
  queued because it has to be *done*, not just scheduled, before answering 200.

## The AI team, in full (module 10)
- **Owned paths** — the specific files/folders a role is allowed to edit; checked by
  reviewers and the `respect-ownership` playbook, not (yet) by a hook.
- **Escalation (`owner-inbox.md`)** — the explicit, named list of decisions that always go
  to the human owner, with options, a recommendation, and a deadline.
- **Token budget** — the shared, exhaustible usage limit across the whole agent team,
  treated explicitly as a cost to be managed (decision 0018), not an afterthought.
- **Model tiering** — assigning `haiku`/`sonnet`/`opus` per task based on how much
  judgment it needs, rather than one model for every role.
- **Guard hook** — `.claude/hooks/guard-bash.py`, a mechanical, unconditional block on a
  specific list of dangerous commands (force-push, tags, deploys, `aws`, secrets),
  distinct from and complementary to the written process rules.
- **Promotion ladder** — the path a recurring lesson takes from a written reminder, to a
  playbook or role-file rule, to a mechanically enforced test or hook, as it keeps
  recurring.
- **Structural fix** — a fix that makes the correct behavior the *default*, so it can't be
  skipped by forgetting a step, as opposed to a written rule that depends on being
  remembered every time.
- **Root-causing a flake** — finding the actual, specific cause of an intermittent failure
  before writing it off as random, since an unexplained "flake" is often a real, repeatable
  bug (a shared Redis DB, a sleeping laptop) hiding behind a misleading label.

## Deploy and ops (module 11)
- **SST (Serverless Stack)** — infrastructure-as-code written in TypeScript, with
  pre-built components for common AWS resources, used for InvAI's AWS configuration.
- **Stage** — SST's name for an environment (`production`, `staging`, `demo`, or an
  ad-hoc name); one config file branches on the stage name rather than using separate
  files per environment.
- **Fargate** — AWS's serverless container-running service; InvAI's Api, Worker, Imaging
  and one-off Migrate processes all run on it, so no EC2 instance is managed directly.
- **`/readyz` vs. `/health`** — a load-balancer-facing readiness check (only the hard
  dependencies that should pull a task out of rotation) versus a human/monitoring-facing
  status check (reports on everything, including degraded-but-not-fatal dependencies).
- **KMS envelope encryption** — AWS's managed key-encrypts-key scheme, production's
  planned upgrade from the static `FIELD_ENCRYPTION_KEY` ring.
- **List price** — a vendor's published, undiscounted price, used in cost estimates
  because no committed-use discount or negotiated rate exists yet.
- **NAT (Network Address Translation)** — lets resources in a private subnet reach the
  internet (or AWS services) without being directly internet-facing.
- **VPC interface endpoint** — a private, paid network path from a VPC directly to a
  specific AWS service, avoiding a trip through NAT or the public internet.
- **Scenario-based estimate** — pricing several concrete configurations instead of giving
  one number, so a cost estimate answers "what does this specific setup cost."
- **`[[OWNER]]` marker** — a notation in ops docs flagging a control that requires the
  human owner's direct action (an account, a credential, a repo setting) rather than
  something an agent can configure in code.
- **P0 (priority zero)** — the highest urgency tag for a gap, meaning it must be fixed
  before a specific risky action is allowed to proceed.
- **SEV1–SEV4** — InvAI's incident severity scale, from PII/cross-tenant exposure or a
  total outage (SEV1) down to a cosmetic issue or near-miss (SEV4).
- **Incident commander (IC)** — the role that directs a live incident (decides, keeps the
  timeline, assigns work) without fixing code itself, kept separate from the fixers.
- **Research gap** — a numbered item in `invai-docs/research/` identifying a known missing
  control; written ops policies and backlog items both trace back to these gap numbers.

## Product and business (module 12)
- **Segment** — one of three named shop profiles (small/mid/large) `scope.md` uses to
  decide what to build for whom, and in what order.
- **SCR (scope-change request)** — the only process allowed to add or change what's in
  `scope.md`, requiring PM approval and, for anything touching cost or risk, the owner's
  approval too.
- **Fence** — a hard limit on *how* an in-scope feature is allowed to behave (not whether
  it exists), set with the owner's approval, such as "no scraping" or "no automatic price
  changes."
- **Trigger (deferred scope)** — the specific, named condition that would bring a deferred
  item back into active consideration.
- **Pricing hypothesis** — a stated price to be tested against real pilot data, not a
  final, settled number.
- **Pricing experiment** — a structured test (hypothesis, segment, offer, a method sized
  to the real sample available, a success metric, a readout plan) for finding out if a
  price works.
- **Confidence cap** — an explicit upper limit research applies to its own certainty when
  it has no real pilot evidence yet, so a desk-research finding isn't mistaken for a proven
  one.
- **Impact × reach × confidence ÷ effort** — the formula used to rank growth ideas against
  evidence rather than intuition.
- **Outside-approval tiebreaker** — the rule that any idea blocked on an approval the team
  doesn't control ranks below every idea that isn't, regardless of its raw score.
- **Don't-build list** — a specific, reasoned list of ideas the research recommends never
  building, each with its own stated mechanism (legal risk, market fit, policy
  impossibility, trust cost).
- **Inducement** — a legal theory of liability for building or providing a tool whose main
  foreseeable use is enabling someone else's infringement.

## Build from zero (module 13)
- **Docker Compose** — a tool that starts a group of containers from one YAML file
  describing each service's image, ports and settings; `invai-infra/local/docker-
  compose.yml` is InvAI's real one.
- **Container** — a lightweight, isolated process running from a packaged image; InvAI's
  local Postgres, Valkey and MinIO all run as containers.
- **Volume (Docker)** — a Docker-managed storage location that survives a container being
  stopped or recreated, as long as it isn't explicitly removed.
- **Contract-first** — writing an API's shapes (inputs, outputs, errors) down once, in a
  shared package, before any backend or frontend code is built against it.
- **Procedure (oRPC)** — one callable unit in an oRPC contract: an input shape, an output
  shape, a permission, and the errors it may throw.
- **ESM (ECMAScript Modules)** — the standard `import`/`export` module system every InvAI
  repo uses, instead of the older CommonJS `require`.
- **Handler** — the function attached to one oRPC procedure that does the real work
  (query the database, return a value, or throw a declared error).
- **Authentication** — proving who is making a request (a valid session); Better Auth's
  job in InvAI.
- **Authorization** — deciding what a known, authenticated requester is allowed to do;
  InvAI's own permission guard, reading `ROLE_PERMISSIONS`, handles this.
- **Permission guard** — the middleware every InvAI procedure passes through, checking
  its declared permission against the signed-in member's role before any handler runs.
- **Adapter** — a concrete implementation of a shared interface for one specific provider
  (a mock, or a real carrier/marketplace/supplier), interchangeable with any other adapter
  of the same interface.
- **Deterministic (mock)** — producing the same output for the same input every time, with
  no randomness or dependence on the current time; a requirement for every InvAI mock
  provider, so tests built on top of them aren't flaky.
- **TanStack Query** — the library managing server-state in InvAI's React apps: caching,
  loading/error states, refetching and cache invalidation after a write.
- **Query key** — the identifier TanStack Query caches a piece of data under; invalidating
  a key tells it that data may be stale and should be refetched.
- **Mutation (TanStack Query)** — a hook for a write (create/update/delete), as opposed to
  a query (a read).
- **Wedge scanner** — a barcode scanner that connects as a keyboard ("keyboard wedge"),
  detected by keystroke timing rather than a special browser API; `invai-floor`'s scan
  listener is built on this.
- **Offline-first** — an app design where every action is written to a local store first
  and synced to the server opportunistically, so the UI never has to block on network
  availability; `invai-floor`'s whole scan flow works this way.
- **Parked (floor outbox sense)** — an outbox entry the flush gave up retrying
  automatically (rejected, blocked, or sign-in ended), surfaced to the person instead of
  retried forever.
- **DPI (dots per inch)** — the resolution a physical size is rendered at;
  `invai-imaging` always derives pixels from inches and DPI, never the other way around.
- **Role file** — a markdown file (with frontmatter) under `.claude/agents/` scoping one
  agent's ownership, model and preloaded skills.
- **Skill (generic)** — a reusable, named checklist an agent loads at a specific point in
  its work (before editing, before reporting done), instead of one long always-on
  instruction set.
- **Hook (generic)** — a script that runs automatically around a tool call, enforcing a
  rule mechanically rather than relying on it being remembered; `guard-bash.py` (see
  "Guard hook" above) is InvAI's real one.
