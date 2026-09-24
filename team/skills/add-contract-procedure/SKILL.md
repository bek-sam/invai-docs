---
name: add-contract-procedure
description: Add or change an oRPC procedure, schema, event or enum in @invai/contracts so backend, web and floor stay in step. Use for "new endpoint", "new procedure", "add a field", "new enum value", "new event" or any change under invai-contracts/src, including the consumer checklist for backend, web and floor.
---

# Add a contract procedure

A contract change lands additive, tested and typechecked in every consumer on the same day, with a named
implementer for each stubbed procedure.

## When to use
- A card needs a procedure, input or output field, error, enum value, outbox event or realtime event that
  `invai-contracts` doesn't have.
- You are the `architect` (owner of `invai-contracts/**`). Backend, web and floor engineers use
  `consumer-checklist.md` in this folder when the change reaches them.
- Removing or renaming anything: use `contract-deprecation` instead.

## Steps
1. **Read** `invai-contracts/README.md` ("How to add a procedure", "The permission model"), the domain files
   `src/contract/<domain>.ts` and `src/schemas/<domain>.ts`, and `src/contract/_base.ts`.
2. **Schema first.** Put entity and input schemas in `src/schemas/<domain>.ts`. Reuse `Id`, `Cents`,
   `Timestamp`, `Page`, `paginated`, `Address` from `src/schemas/common.ts`. Export `type X = z.infer<typeof X>`.
3. **Procedure.** In the namespace router of `src/contract/<domain>.ts`:
   ```ts
   hold: proc("orders.manage")                       // permission from src/roles.ts
     .route({ method: "POST", path: "/{id}/hold" })  // path params must be input keys
     .input(z.object({ id: Id, reason: z.enum(HOLD_REASONS) }))
     .output(OrderWithItems)
     .errors({ ALREADY_HELD: { status: 409, message: "Order is already on hold" } }),
   ```
   - `auth`: `user` (default), `floor` (tablet session may call it), `station` (station token only), `public`.
   - Reuse an existing permission when the meaning matches. A new permission goes in `PERMISSIONS` and
     `ROLE_PERMISSIONS` in `src/roles.ts`.
   - Lists take `Page.extend({...filters})` and return `paginated(Item)`. Async work returns `JobRef { jobId }`.
   - Scans and other business outcomes return a result (`ScanResult` with `mismatch`, `nextAction`). They
     never throw.
4. **New namespace** only if no domain fits: `base.prefix("/<path>").tag("<domain>").router({...})`, added to
   `contract` in `src/contract.ts`, schemas exported from `src/index.ts`.
5. **Events.** A new outbox event goes in `Events` (`src/events.ts`). If a screen must refresh, also add it to
   `RealtimeEvents` (`src/realtime.ts`) and tell web-engineer to map it in `invai-web/src/lib/realtime.ts`
   `keysForEvent()`.
6. **Enum values go at the end.** For each new value, grep the consumers for exhaustive switches and list the
   files in your report:
   ```
   grep -rn "<EnumName>\|<existing value>" ../invai-backend/src ../invai-web/src ../invai-floor/src ../invai-ui/src
   ```
   (A new mismatch reason once broke the floor this way.)
7. **Test** in `invai-contracts`: `pnpm typecheck && pnpm lint && pnpm test`. `src/contract.test.ts` checks
   route, known permission, unique method + path and pagination. Add tests for new state transitions
   (`src/states.test.ts`) and schema round-trips (`src/schemas.test.ts`).
8. **Typecheck every consumer** against your working copy (they use `link:../invai-contracts`):
   ```
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
   for r in invai-backend invai-web invai-floor invai-ui; do (cd ../$r && pnpm typecheck) || echo "BROKEN: $r"; done
   ```
   A new procedure shows up in the backend as NOT_IMPLEMENTED through `stubRouter()` (`src/api/orpc.ts`) until
   the implementer fills it. A type break is yours to report the same day.
9. **Update** the README module map or namespace table if you added a file, namespace or permission.
10. **Report** per consumer, using `consumer-checklist.md`: what each repo must do, the implementer's name,
    and the enum-switch files from step 6.

## Rules (MUST / MUST NOT)
- MUST be additive: new optional fields, new procedures, enum values at the end. Web SPA and floor PWA may run
  one version behind the API for hours (research 11 §4.2).
- MUST give every procedure a permission, `auth`, `.route()`, input and output schemas, its domain errors and
  a named implementer.
- MUST keep conventions: cents, inches (numeric, never rounded), `*Pct` percents, 0..1 ratios, ISO timestamps,
  UUIDs; shop words (blank, transfer, gang sheet, station, bin, tote).
- MUST keep `permission: "none"` limited to the five auth-bootstrap procedures (`contract.test.ts` enforces
  this).
- MUST NOT add runtime code beyond schemas, constants and pure helpers.
- MUST NOT edit consumer repos to absorb your change. Their owners do it (`respect-ownership`).
- MUST record an ADR (`record-decision`) for anything cross-cutting: a new namespace, a new auth mode, a new
  state.

## Done when
- `pnpm typecheck && pnpm lint && pnpm test` pass in `invai-contracts`.
- Backend, web, floor and ui typecheck against the change, or each break is listed with its owner.
- The report lists each new procedure with its implementer and every consumer file to change.
- Co-review requested: `reviewer` on a different model, plus backend-foundation and one consumer engineer.

## References
- `consumer-checklist.md` (this folder)
- `invai-contracts/README.md`, `src/contract/_base.ts`, `src/contract.test.ts`
- `invai-backend/src/api/orpc.ts` (`stubRouter`), `src/api/authz.test.ts` (walks every procedure)
- `invai-docs/research/12-security-quality-playbook.md` §1.3, §3.3
- Related: `contract-deprecation`, `add-backend-feature`, `build-dashboard-screen`, `build-floor-flow`
