# Lesson 13.2 — A repo and the contract package: Zod + oRPC, first procedure

## 1. In one sentence
You'll create a tiny TypeScript package that defines one API procedure — its inputs,
outputs and errors, with no backend behind it yet — using Zod for the shapes and
oRPC's contract builder to turn them into something both a server and a client can
agree on, exactly the role `@invai/contracts` plays for all of InvAI.

## 2. Why it exists
In most small projects, "the API" is just whatever the backend happens to return,
and the frontend finds out it's wrong when something crashes at runtime. InvAI's rule
is **contract-first**: the shape of every request and response is written down once,
as code, in its own package — before the backend implements it and before the
frontend calls it. That one file becomes the single source of truth both sides import
from, so a backend typo in a field name becomes a *compile error* in the frontend, not
a production bug a shop owner reports.

The "change order" rule in `CLAUDE.md` exists because of this: `invai-contracts` →
`invai-backend` → `invai-web`/`invai-floor`. A breaking contract change has to be
fixed in every consumer the same day, which is only possible because there's exactly
one contract everyone agrees to point at.

## 3. How it works

### Step 1 — the package
```bash
cd ~/invai-from-zero
mkdir contracts && cd contracts
pnpm init
pnpm add zod@^4.6 @orpc/contract@^1.15
pnpm add -D typescript
```
`package.json` needs `"type": "module"` (InvAI is ESM throughout) and a build/export
setup — for this exercise, a single `src/index.ts` is enough; you don't need a bundler
yet.

### Step 2 — a schema with Zod
Zod v4 describes a shape and gives you a TypeScript type for free. Make
`src/schemas.ts`:
```ts
import { z } from "zod";

export const Id = z.uuid();

/** Money is always integer cents — never a float dollar amount. */
export const Cents = z.number().int();

export const Widget = z.object({
  id: Id,
  name: z.string().min(1),
  priceCents: Cents,
});
export type Widget = z.infer<typeof Widget>;
```
Run `npx tsc --noEmit` (or just import it in a scratch file) and notice: you now have
both a runtime validator (`Widget.parse(someUnknownValue)`) and a compile-time type
(`Widget`), generated from the same four lines.

### Step 3 — a procedure with oRPC's contract builder
`oc` (oRPC contract) chains `.input()`, `.output()`, `.errors()` and `.route()` to
describe one callable procedure without writing any server code. Make
`src/contract.ts`:
```ts
import { oc } from "@orpc/contract";
import { z } from "zod";
import { Id, Widget } from "./schemas";

const COMMON_ERRORS = {
  NOT_FOUND: { status: 404, message: "Not found" },
} as const;

const base = oc.$meta<{ permission: string }>({ permission: "none" }).errors(COMMON_ERRORS);

export const widgets = base
  .prefix("/widgets")
  .router({
    get: base
      .meta({ permission: "widgets.read" })
      .route({ method: "GET", path: "/{id}" })
      .input(z.object({ id: Id }))
      .output(Widget),

    create: base
      .meta({ permission: "widgets.write" })
      .route({ method: "POST", path: "/" })
      .input(z.object({ name: z.string().min(1), priceCents: Cents }))
      .output(Widget),
  });

export const contract = { widgets };
```
Notice what you *didn't* write: no database call, no Express/Hono route handler, no
HTTP client. This file describes the shape of an interaction, nothing else — that's
the whole point of "contract-first."

### Step 4 — see it fail honestly
```ts
// scratch.ts
import { widgets } from "./src/contract";
widgets.get.input; // hover in your editor: Zod infers { id: string } (uuid-shaped)
```
Try calling `.input()` on something that doesn't match (e.g. pass a plain `string()`
schema where `Widget` output expects an object) — the TypeScript error you get *before
running anything* is the entire value of this pattern: a contract mismatch is caught
at compile time, in your editor, not at 2am in production logs.

## 4. In our code
- `invai-contracts/src/contract/_base.ts:95-102` — the real `base`/`proc()` helpers:
  `export const base = oc.$meta<ProcedureMeta>({ permission: "none" }).errors(COMMON_ERRORS)`
  and a `proc(permission, opts)` wrapper that's exactly the `.meta({ permission, ...opts })`
  call you wrote by hand above, just factored into a reusable function.
- `invai-contracts/src/contract/_base.ts:23-35` — `COMMON_ERRORS`, the real error map
  every procedure inherits (`UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`,
  `INVALID_TRANSITION`...) — your two-error map above is the same idea at 1/10th the
  size.
- `invai-contracts/src/contract/tenancy.ts:22-30` — a real procedure,
  `me.get`, built the same way: `proc("none", { auth: "floor" }).route({ method: "GET",
  path: "/" }).input(z.object({})).output(Me)`.
- `invai-contracts/src/schemas/common.ts:1-15` — the real `Id`, `Cents`, `Timestamp`,
  `Inches`, `Ratio` primitives your `Widget` schema echoed; every money field in InvAI
  is exactly `z.number().int()` cents, never a float.
- `invai-contracts/src/contract.ts:23-40` — the real top-level `contract` object: one
  key per domain router (`me`, `orders`, `shipping`, ...), assembled from ~20 files the
  same way your `{ widgets }` object assembled one.

## 5. What it uses
- **Zod v4** — runtime validation plus inferred TypeScript types from one
  declaration; module 03.1 covers why this over writing types and validators
  separately (they drift).
- **oRPC's contract package (`@orpc/contract`)** — the piece that turns a tree of
  Zod schemas into something a server can `implement()` and a client can call with
  full type safety on both ends; module 03.1 covers the alternatives InvAI
  considered (tRPC, raw REST + OpenAPI) and why oRPC won.
- **TypeScript strict mode / ESM** — every InvAI repo is ESM (`import`/`export`, no
  `require`) with `strict: true`, which is what makes a contract mismatch a compile
  error instead of a runtime surprise.

## 6. Try it yourself
1. Add a third procedure, `widgets.list`, with `.input(z.object({ cursor:
   z.string().optional() }))` and `.output(z.object({ items: z.array(Widget),
   nextCursor: z.string().nullable() }))`. Then open
   `invai-contracts/src/schemas/common.ts` and find the real `paginated()` helper that
   generates exactly this shape for every list endpoint in InvAI — refactor your
   `list` to use an equivalent helper instead of writing it by hand twice.
2. Deliberately break your `Widget.output`: change `priceCents: Cents` to
   `priceCents: z.string()`. Nothing runs yet, but open the file in your editor and
   watch for a type error the moment anything tries to construct a `Widget` with a
   number. This is the compile-time check a backend implementation will lean on in
   lesson 13.3.
3. Run `npx tsc --noEmit` on your package and get it to pass clean, the same gate
   `pnpm typecheck` runs for `invai-contracts` before anything is allowed to depend on
   it.

## 7. Common mistakes
- Reaching for a remembered oRPC or Zod API instead of checking the installed
  version. InvAI's own `read-before-change` skill exists because of this exact
  failure mode — "code written against the wrong library API" is a named v1 lesson.
  Zod v4's API (`z.email()`, `z.iso.datetime()`, errors as `.issues` not `.errors`)
  differs from Zod v3 tutorials you may have seen before.
- Putting a database call or any side effect inside the contract package. The whole
  value of contract-first is that this package has *zero* runtime behavior — it's
  pure shape description. Side effects belong in the backend that implements it
  (lesson 13.3).
- Skipping `.errors()` and letting a procedure only ever "succeed." InvAI's contract
  declares every error a caller might get (`NOT_FOUND`, `FORBIDDEN`, ...) as part of
  the contract itself, so a backend that forgets to handle a case is caught by the
  type system, and a frontend can exhaustively handle every declared error.

## 8. Check yourself
<details>
<summary>1. What's different between a type you write by hand (<code>type Widget =
{ id: string; ... }</code>) and <code>z.infer&lt;typeof Widget&gt;</code>?</summary>

The hand-written type only helps TypeScript's compiler; it has no runtime check.
`z.infer` is derived from a Zod schema that can also *validate* real data at runtime
(`Widget.parse(unknownValue)`), so the type and the validation can never drift apart —
change the schema and both update together.
</details>

<details>
<summary>2. Why does the "change order" rule (contracts → backend → web/floor)
exist, and what would go wrong without it?</summary>

Because every consumer (backend, web, floor) imports its types and runtime shapes
from the one contract package. If a web screen were built against a field the
backend hadn't implemented yet (or vice versa), either side is referencing something
that doesn't really exist — the order ensures the shared truth exists first, so every
later step is building against something real, not a guess.
</details>

<details>
<summary>3. Your contract declares <code>NOT_FOUND</code> as a possible error for
<code>widgets.get</code>. What happens if the backend that implements it never
actually throws that error for a missing widget?</summary>

Nothing breaks at the type level — declaring an error is optional to actually throw.
But it's a real gap: a caller handling `NOT_FOUND` per the contract would never see
it fire, and a missing widget would surface as some other, probably less helpful,
error (or a crash) instead. The contract describes what's *possible*, not a guarantee
the implementation got it right — that's what tests (lesson 13.10) are for.
</details>

## 9. Words to know
- **Contract-first** — writing down an API's shapes (inputs, outputs, errors) in one
  shared package before any backend or frontend code exists against it.
- **Zod** — a TypeScript-first schema library: one declaration gives you both a
  runtime validator and a static type.
- **oRPC** — the RPC framework InvAI builds its contract and backend/client on;
  `@orpc/contract` is its "describe the shape" half.
- **Procedure** — one callable unit in an oRPC contract (like `widgets.get`): an
  input shape, an output shape, a permission, and the errors it may throw.
- **ESM** — ECMAScript Modules, the standard `import`/`export` module system; every
  InvAI repo uses it instead of the older CommonJS `require`.
