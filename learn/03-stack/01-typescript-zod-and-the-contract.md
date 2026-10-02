# Lesson 3.1 — TypeScript, Zod, oRPC and Biome: the shared backbone

## 1. In one sentence
Every TypeScript repo in InvAI (6 of the 8) agrees on one language (TypeScript), one way to
describe data shapes (Zod), one way to turn those shapes into a callable API
(oRPC) and one tool to keep the code tidy (Biome) — so a change in one repo is caught by the
type checker in every other repo before it ever reaches a person.

## 2. Why it exists
Module 02 showed *where* oRPC and Zod sit in the request flow. This lesson answers the
question a learner should ask next: **why these, and not the other options?** InvAI's own
research docs (`invai-docs/research/06-tools-backend.md`) scored each option before building
started — this lesson is built from those real comparisons, not from general opinion. Knowing
*why* a tool was picked tells you what problem it's there to prevent, which is more useful than
memorizing its API.

## 3. How it works

### TypeScript — one language, strict mode, everywhere
All 6 non-Python repos (`invai-contracts`, `invai-backend`, `invai-web`, `invai-floor`,
`invai-ui`, `invai-infra`) run **TypeScript 7.0.2** (`invai-backend/package.json` —
`"typescript": "^7.0.2"`). TypeScript 7 is the native (Go-ported) compiler, newer than most
training data, which is why `read-before-change`'s library table calls it out by name: a new
compiler error is usually the compiler being right about *this* version, not a reason to reach
for `as any`.

Strict TypeScript means every function's input and output types are checked, not just
suggested. Combined with oRPC (below), this is what makes "the contract didn't change, but
the backend did" into a compile error in `invai-web` and `invai-floor`, instead of a runtime
surprise a shop hits in production.

### Zod — one schema language for validation *and* types
Every procedure's input, output and shared data shape in `@invai/contracts` is a **Zod v4**
schema (`invai-contracts/package.json` — `"zod": "^4.6.5"`). One Zod schema gives you three
things at once: a TypeScript type (via `z.infer`), a runtime validator (rejects bad data at
the API boundary) and — because oRPC is Standard-Schema aware — the shape that drives the
client's typed call signature. An example of the v4 API in real use:
`invai-contracts/src/schemas/orders.ts:39` — `buyerEmail: z.email().nullable()` — Zod v4
moved email validation out of `.string().email()` (the old chained form) into its own
top-level `z.email()`.

Research comparison (`invai-docs/research/06-tools-backend.md:153`): Zod v4 scored **9.5/10**
against Valibot (8) and ArkType, specifically because it's the schema library every other
piece of the stack already expects — oRPC, Hono's `zod-openapi`, Better Auth and the AI SDK
all assume Zod by default. Picking a "faster" or "smaller" validator would have meant writing
glue code at every one of those seams for no real benefit.

### oRPC — contract-first, not code-first
`invai-docs/research/06-tools-backend.md:43-50` compares oRPC against **tRPC v11** and
**GraphQL**:
- GraphQL scored **4/10** — "overkill for a solo developer: N+1 problems, auth per resolver,
  caching... a poor match for print-shop integrators."
- tRPC scored **7.5/10** — the most proven option, but "not REST" — a public API for vendors
  or future integrators would need a separate layer bolted on.
- **oRPC scored 9/10** — contract-first (the shape is declared once, not inferred from a
  function signature), **built-in OpenAPI generation** from the same procedures (useful later
  for a public REST API to print-shop integrators), first-class TanStack Query support, and
  it accepts any Standard Schema library (so swapping Zod later wouldn't mean rewriting oRPC
  code). The tradeoff: "younger than tRPC and a smaller community" — accepted because the
  contract-first shape fits InvAI's actual need (one contract, three consuming repos) better
  than tRPC's code-first inference does.

In practice this means: `invai-contracts/src/contract.ts` is the one file that says what every
procedure looks like, *before* any backend handler exists. `invai-backend/src/api/orpc.ts:34`
— `export const os = implement(contract).$context<Context>();` — builds the actual router by
implementing that already-declared contract. A procedure with no handler yet isn't a type
error; it's a `stubRouter` 501 (`invai-backend/src/modules/README.md`'s router pattern) —
you can see the whole contract compile before a single line of business logic exists.

### Biome — one fast tool instead of two slow ones
Every TypeScript repo runs the identical formatter/linter config
(`invai-backend/biome.json:1-17` — one JSON schema pinned to `2.5.14`, 2-space indent, 100-char
lines, the `recommended` rule preset). Research (`06-tools-backend.md:149-163`) scored
**Biome 8.5/10** against "ESLint + Prettier" at 7.5: "one fast tool... v2 adds type-aware
rules such as floating-promises" — important here because job handlers
(`invai-backend/src/modules/*/jobs.ts`) are exactly the kind of code where a silently dropped
promise (an `await` you forgot) causes a job that looks like it ran but didn't. ESLint +
Prettier remains an option *only* "if you need rules Biome lacks" — the project hasn't needed
that yet.

## 4. In our code
- `invai-contracts/src/contract.ts:28-50` — the contract object every repo imports; this is
  the "one shape" oRPC's contract-first design depends on.
- `invai-contracts/src/contract/_base.ts:15-20` — `ProcedureMeta`, every procedure's
  permission/auth metadata, typed through the same Zod-adjacent system.
- `invai-contracts/src/schemas/orders.ts:39` — a real Zod v4 call (`z.email()`), worth
  comparing against older Zod code you might see in tutorials (`.string().email()`).
- `invai-backend/src/api/orpc.ts:34,127` — the contract implemented into a router, and the
  one-line permission guard every procedure passes through.
- `invai-backend/biome.json:1-17` — the one Biome config every repo's `pnpm lint` reads.
- `invai-backend/package.json`, `invai-contracts/package.json` — the exact pinned versions
  (`typescript@^7.0.2`, `zod@^4.6.5`, `@orpc/server@^1.15.4`, `@biomejs/biome@^2.5.14`).

## 5. What it uses
- **TypeScript 7** — the Go-ported native compiler; strict mode across all 6 TS repos.
- **Zod v4** — schema, validation and type inference in one, and the default for every
  adjacent library (oRPC, Better Auth, the AI SDK).
- **oRPC 1.15.4** — contract-first RPC with built-in OpenAPI generation and TanStack Query
  support; chosen over tRPC (not REST-shaped) and GraphQL (operational overkill for this
  team's size).
- **Biome 2.5.14** — one fast formatter+linter, including type-aware rules that catch
  floating promises; ESLint+Prettier stays the fallback only for rules Biome lacks.

## 6. Try it yourself
1. Open `invai-contracts/src/contract/orders.ts` and find one procedure's Zod input schema.
   Then open the matching handler in `invai-backend/src/modules/orders/router.ts` and confirm
   the handler's `input` parameter is typed from that schema — you never wrote that type by
   hand.
2. Run `cd invai-backend && export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH" && pnpm lint 2>&1 | tail -n 20` — a clean run is Biome checking every file against
   `biome.json` in one pass.
3. In `invai-contracts/src/schemas/orders.ts`, search for other `z.` calls near line 39 (e.g.
   `z.uuid()`, `z.iso.datetime()` if present) — these are Zod v4's newer top-level helpers;
   compare them mentally to how you'd have written them in Zod v3 (chained off `.string()`).

## 7. Common mistakes
- Writing Zod code the way an older tutorial (or an LLM trained before Zod v4) shows it —
  e.g. `z.string().email()` instead of `z.email()`. It still often works for backward-compat
  reasons, but `read-before-change`'s whole point is: check `node_modules/zod` for the
  *installed* version's real API before copying a pattern you remember.
- Assuming a contract change is "just a type that updates itself." Per `CLAUDE.md`'s change
  order, a breaking contract change must be fixed in every consumer **the same day** — `
  invai-contracts` → `invai-backend` → `invai-web`/`invai-floor`. The type checker will catch
  the mismatch, but it won't fix the other two repos for you.
- Treating Biome's `recommended` preset as a ceiling. It's deliberately the smaller, faster
  option (research score 8.5 vs. ESLint+Prettier's 7.5) precisely because the team didn't need
  every ESLint rule — but if a specific rule class is genuinely missing, the fallback is a
  minimal ESLint pass alongside Biome, not silencing the warning.

## 8. Check yourself
<details>
<summary>1. Why did oRPC beat tRPC for InvAI specifically, given tRPC is "the most proven
option"?</summary>

tRPC is code-first (types inferred from handler functions) and "not REST" — a public API
would need a third-party layer. oRPC is contract-first and generates OpenAPI from the same
procedures used internally, which matters because InvAI may eventually expose a public API to
print-shop integrators.
</details>

<details>
<summary>2. What three things does one Zod schema give you at once?</summary>

A TypeScript type (via `z.infer`), a runtime validator at the API boundary, and (through
Standard Schema) the shape oRPC uses to generate a typed client call signature.
</details>

<details>
<summary>3. A procedure exists in the contract but has no backend handler written yet. What
happens if a client calls it — a type error, a crash, or something else?</summary>

A 501, via `stubRouter` (`invai-backend/src/modules/README.md`'s router pattern) — the
contract compiles and the route exists, it just isn't implemented yet. This is what lets the
whole contract "exist" before every handler is built.
</details>

## 9. Words to know
- **Standard Schema** — a shared interface multiple validation libraries (Zod, Valibot,
  ArkType) implement, so a tool like oRPC can accept any of them without hard-coding one.
- **Contract-first** — the API's shape is declared once, in a schema, *before* any handler is
  written; the opposite of "code-first," where types are inferred from function signatures.
- **`stubRouter`** — an oRPC helper that returns a 501 for any contract procedure without a
  real handler yet, so an unfinished module still type-checks and runs.
