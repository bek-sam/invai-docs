# T-4-2: The floor offline queue never jams

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` item 5 |
| Backlog | B-95 |
| Owner | floor-engineer |
| Reviewer | reviewer; co-reviewers qa-engineer, security-reviewer |
| Risk flags | floor-correctness |
| Model | opus |

## Owned paths
- `invai-floor/src/outbox/**` (the real DB file is `src/outbox/db.ts` — the earlier `src/app/db.ts` in this card was wrong, there is no such file), `src/app/actions.ts`, `src/components/SyncStatus.tsx`, `src/screens/LoginScreen.tsx` (or wherever "forget this station" lives)
- New `invai-floor/e2e/offline.spec.ts`. qa-engineer co-owns it and reviews it.
- Your own i18n keys (hand edit, commit only your hunks)

## Evidence
`build/audit-2026-09-24.md` §A-FE B-95 (`outbox.ts:101,108,118`, `SyncStatus.tsx:47`, `actions.ts:213`, `LoginScreen.tsx:101`).

## Correction (architect r1)
`OutboxEntry.attempts` and `OutboxEntry.lastError` already exist (`outbox/db.ts:24-25`) — only `parkedAt: string | null` and a new `"parked"` value on `OutboxStatus` are new. **No Dexie version bump is required**: Dexie doesn't need an upgrade for a new unindexed field or a new value inside an already-indexed field (`status` is indexed today; its allowed TS values are not enforced by Dexie). Treat `entry.parkedAt === undefined` on pre-existing rows the same as `null` everywhere you read it. Only bump to `version(3)` (with `outbox: "++seq, &id, status, parkedAt"`) if you specifically want `parkedAt` indexed for the Problems Sheet query — Dexie back-fills old rows with an undefined index key with no upgrade function needed, so this is optional, not required for correctness.

## Acceptance criteria
1. **Parking:** a 5xx, 408 or 429 retries with backoff, up to 5 attempts, then the entry is parked. Any other 4xx parks at once. A parked entry never blocks later entries.
2. **Problems sheet:** tapping the sync badge opens a sheet listing pending and parked entries: what, when, who and the error, translated. A lead or admin can retry or discard a parked entry. The badge counts only unresolved entries, and synced entries are pruned.
3. **Rejected replays:** a replayed command that the server rejects (QC, bin, reprint, scan `BLOCKED`) raises a visible, translated alert with the unit, not just a count.
4. **Attribution:** every entry stores its staff session. If that session was revoked, the replay is sent attributed to the original staff with a flag, or it's parked for a lead to confirm. It's never credited to whoever is signed in now.
5. **Forgetting the station:** "Forget this station" with pending entries warns, and needs an explicit confirm that states the count. Pending entries from a forgotten station are never replayed under the next station.
6. **Storage:** `navigator.storage.persist()` is requested at pairing.
7. **E2E `offline.spec.ts`:** go offline → scan 3 units → one server-rejected entry → reconnect → 2 sync, 1 parked, the alert shows, and nothing jams.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in floor.
- The new E2E against your own API and floor on a DB copy.
- Screenshots of the problems sheet in en and es.
