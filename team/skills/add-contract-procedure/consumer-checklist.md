# Consumer checklist for a contract change

Each consumer owner works through its section the same day the contract lands. Tick each line or write N/A with a reason.

## Backend (`backend-engineer` for the module, `backend-foundation` for core)
- [ ] `pnpm typecheck` in `invai-backend` passes against the new contract.
- [ ] The new procedure is implemented in `src/modules/<area>/router.ts` (one line: `withTenant` + service call), or it stays on `stubRouter()` with the card that will fill it named in the report.
- [ ] Input is trusted only after the contract's Zod parse. Foreign ids in the input are loaded under `withTenant` (S-26 is open: FKs don't check the tenant).
- [ ] Output goes through a `toX()` mapper that matches the output schema exactly: ISO strings from `timestamptz`, numbers not strings for `numeric`, cents as integers.
- [ ] Domain errors thrown with `src/lib/errors.ts` helpers, or `ORPCError` with the code the contract declares.
- [ ] A new outbox event is emitted with `emit(tx, companyId, name, payload)` inside the transaction; a realtime event is published through `afterCommit`.
- [ ] `src/api/authz.test.ts` still passes (it walks every procedure as anonymous, no-permission, floor, station and vendor).
- [ ] A cross-tenant test: company B asks for company A's id and gets `NOT_FOUND`.
- [ ] Curl as the right role on your own port (see `add-backend-feature`).

## Web (`web-engineer`)
- [ ] `pnpm typecheck && pnpm build` in `invai-web` pass.
- [ ] Every exhaustive `switch` or `Record<Enum, ...>` over a changed enum has the new value (grep the enum name and an existing value).
- [ ] New realtime event mapped in `src/lib/realtime.ts` `keysForEvent()` so the right queries refresh.
- [ ] Nav or buttons gated on the procedure's permission through `useCan()` (`src/lib/me.ts`), never on role names.
- [ ] A procedure that is still a stub renders the calm "coming soon" `ErrorState` (`src/components/states.tsx`), not a crash.
- [ ] New strings in en and es (`pnpm i18n`).

## Floor (`floor-engineer`)
- [ ] `pnpm typecheck && pnpm build` in `invai-floor` pass.
- [ ] The `FloorApi` interface (`src/api/types.ts`) and **both** implementations are updated: the oRPC one (`src/api/rpc.ts`) and the demo backend (`src/api/demo.ts`). The demo must follow the same rules as the server.
- [ ] New scan result or mismatch values are handled in `src/scan/result.ts`, `src/scan/pressFlow.ts` and the station screens, with en and es strings (`src/i18n/en.ts`, `es.ts`). A new blocking reason must still block.
- [ ] Offline outbox: a new write command gets a stable id so a replay is idempotent (`src/outbox/outbox.ts` `commandId()`).

## UI kit (`product-designer`, `invai-ui`)
- [ ] `StatusBadge` and `ChannelBadge` cover any new `OrderItemState` or `Channel` value, with en and es in `src/i18n/locales/`.

## Contract author (`architect`)
- [ ] Report lists: new procedures and their implementers, changed enums with the consumer files found by grep, and events added.
