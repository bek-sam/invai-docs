# Architect plan review: wave P2

**Verdict: approve-with-changes**

Ownership and grants check out across all five cards: no two cards touch the same file (T-P2-2's grants into
`integrations/imaging/client.ts`, `production/router.ts` and `orders/*.test.ts` are narrow and named; T-P2-5
stays inside `modules/today/**`). Port/Redis slots don't collide (T-P2-2: API :3122, imaging :8022, Redis
db 12; T-P2-5: Redis db 11, API :3125). No new permissions or enum values in this wave, so no exhaustive-switch
fan-out to list.

## Rulings

1. **T-P2-4, re-scope now, don't ship AC2 as written.** The "no contract change" premise holds only for AC1.
   `from`/`to` really are typed on `TimelineEntry` (`invai-contracts/src/schemas/orders.ts:230-231`). The
   reason text is not: `orderItemTransitions.reason` (free text, e.g. `floor.ts:636` `reprint: ${code}`) is
   folded only into the composed English `message` string (`orders/service.ts:639`); `meta` is `t.data`,
   which `transitionItem` never copies `opts.reason` into (`state-machine.ts:70-78`). To satisfy AC2 inside
   its own owned path (`order-detail.tsx` only, backend/contracts read-only), web would have to regex the
   backend's free-text message to recover `scan match` / `other` / `reprint: <code>` — a hidden coupling to
   an untyped string format, not a contract. Ship AC1 (from/to) this wave; defer AC2 to the same follow-up as
   B-224, with a tiny additive field instead of string-parsing: `reasonCode: string | null` on `TimelineEntry`,
   filled 1:1 from the existing `t.reason` column in `orders/service.ts`. I'll own that addition when B-224
   is scheduled.

2. **wave.md Slots table, add T-P2-4.** The table sequences the shared :3000/:5173 slot as
   T-P2-1 → T-P2-3 → gate, but T-P2-4's own card claims that same slot "after T-P2-1 frees it." Add T-P2-4
   into the documented order (T-P2-1 → T-P2-3 → T-P2-4 → gate) so the tech lead doesn't schedule qa-engineer
   and web-engineer on the same ports at once.

3. **T-P2-2 design is sound**, verified against the code: short read tx → `imaging.preview()` with no tx
   open → per-file short write tx guarded by a `file_key` match (the stale-thumbnail-after-replace case),
   `isCompanyKey` kept before every call, deterministic `designPreviewKey` keeps a retried whole-design job
   idempotent even if earlier files in the loop already succeeded. Checked the one caller outside catalog's
   grant, `db/seed/builder.ts:535-541`: it already wraps `imaging.preview()` in try/catch and sets
   `previewKey: null` on failure, so making `preview()` throw on transient errors doesn't regress it — note
   this explicitly in the report since that file sits outside the card's owned paths and grants.

4. **T-P2-5 BullMQ semantics check out**: `Queue.getJob`, `Job.getState()` and `Job.remove()` all exist in
   the installed 6.3 types (`queue-getters.d.ts`, `job.d.ts`), so get-state-then-remove-then-enqueue for a
   `failed` job is valid; the `(company_id, date)` row stays the real idempotency guarantee. Add a defensive
   try/catch around `job.remove()` for the race where a second concurrent sweep already removed/retried the
   same job between the state check and the remove call — it should no-op, not throw.

5. **B-224 deferral is correct, not just convenient.** Today alert `title`/`message` are fully composed
   English sentences with no code/params field at all (`today/service.ts:321-394`), unlike T-P2-4's `from`/`to`
   — there is no way to translate them without a contract change. Keep it next wave, architect first, as
   planned.
