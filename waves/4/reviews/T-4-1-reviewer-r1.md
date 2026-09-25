# Review of T-4-1 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: backend-engineer (production) on Claude Opus 5.5 (backend `c839e93`, `d45e155`, `bdffe6f`); architect on Claude Sonnet 5 (stubs contracts `c181abf`, backend `e427b8f`)
- Verdict: **approve** (backend). The contract's stale comments are blocking in `T-4-1-architect-r1.md`, not here.
- Model note: I run on the same model as the backend author. The card's risk flag (floor-correctness) doesn't require a different model, and the stubs were reviewed on a different model (Opus vs Sonnet). The tech lead can ask for a Fable pass if they want one.

## Evidence I re-ran
Worktree `invai-backend-r41` at `bdffe6f`, with `node_modules` symlinked. Test DB `invai_test_r41`, Redis db 9.

| Command | Result |
|---|---|
| `tsc --noEmit` (backend) | exit 0 |
| `biome check .` (backend) | 242 files, no fixes |
| `vitest run` (backend, full suite) | 63 files, 447 tests passed |
| `tsup` (backend build) | Build success |
| contracts: `vitest run` / `tsc --noEmit` / `biome check .` | 4 files, 31 tests passed / exit 0 / 46 files clean |
| web `tsc --noEmit`, floor `tsc --noEmit` against contracts `c181abf` | clean, clean |
| `scan-test-weakening.sh invai-backend f036fbd` | no hits (0 removed, 72 assertion lines added) |
| `scan-test-weakening.sh invai-contracts 11f53f5` | no hits |
| `pack.test.ts` from `bdffe6f` run against `d45e155` code | **2 failed** (hand-off `packed:false`, status never lifted), 10 passed. The round-2 tests prove the round-2 change. |
| API :3191 on `invai_r41_copy` (a copy of `invai`, migrated, "up to date") | see the rows below |
| QC-pass 1 of 3 pressed units, then `POST /production/pack-order` as packer | `409 PACK_INCOMPLETE`, `defined:true`, `missing` = the 2 pressed units |
| DB after the refusal | status `in_production`, `pack_override` null, 0 `floor_requests`, 0 pack scans, 0 audit rows. **No side effects.** |
| QC-pass the other 2, assign tote `R41A`, same call and same key | `200 {packed:true, missing:[], override:null}` |
| Replay, same key | byte-identical body (`cmp` IDENTICAL) |
| Same key on another order | `409 CONFLICT` |
| DB after the pack | `ready_to_ship`; 1 `floor_requests` row; 3 pack scans; 1 `order.packed` audit; `R41A` released; pack queue for the order: 0 |
| Hand to lead as packer (`override.reason`) | `403 FORBIDDEN` (`production.override`); the tote is still assigned, no override, 0 rows, 0 audit rows |
| Hand to lead as admin | `200 packed:false`, `missing` = 2, `override` = `{reason, by, byName:"Alex Admin", at, missingItemIds}` |
| Replay / other reason / same key without override | IDENTICAL / `409 CONFLICT` / `409 CONFLICT` |
| DB after the hand-off | status still `in_production`; `pack_override` set; tote `R41L` released; 0 pack scans; audits `order.pack_override` and `order.handed_to_lead`; not in `GET /shipping/queue` |
| The lead QC-passes the 2 missing units | `ready_to_ship`, `pack_override` cleared; a normal `packOrder` with a new key: `packed:true`, 3 pack scans |
| `sheets/{id}/received` as receiver / as office | `200 received` / `200 received` (the sheet's items move to `transfer_in`) |
| receiver `sheets/{id}/cancel`, `.../regenerate`; presser `.../received` | `403` (`production.build`), `403`, `403` (`production.receive`) |
| Press scan: CC1717 transfer + BC3001 blank as presser | `ok:false, mismatch:"wrong_style"`, "Wrong style: needs Comfort Colors 1717 Crimson M, scanned Bella+Canvas 3001 Black S"; the unit stays `transfer_in` |
| Scan at `station:"receiving"` | `ok:false, wrong_station`, "This station doesn't scan transfers" |
| QC pass replayed on a packed unit; bin assign ×2, release ×2 | `200`, state `packed`, 5→5 transitions; one bin row, released |
| RLS as `invai_app` on `floor_requests` | no tenant: 0 rows; other tenant: 0 rows; own tenant: 3 rows; inserting another `company_id` violates the RLS policy |

Cleanup: API stopped, port 3191 free; `invai_r41_copy` and `invai_test_r41` dropped; Redis db 9 flushed; the worktree and `/tmp` files removed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 packOrder refuse / pack / replay / no tote | Yes | curl rows above; `pack.test.ts:92,139` (no-tote retry at `:139`) |
| 2 Override (as amended by decision 0010: hand to lead, no forced `ready_to_ship`) | Yes | packer 403, admin 200 `packed:false` + `missing[]` + `override`; audited; tote released; status unchanged; self-clears. `pack.test.ts:168,410` |
| 3 `wrong_style` no regression | Yes | live press scan above; `matcher.test.ts` in the green suite |
| 4 QC/bin idempotent | Yes, **as amended by the tech lead** (state-based, no contract key) | QC replay: 200 with no new transition; bin double tap: one row. `production.test.ts:287,342`, `pack.test.ts:336`. The amendment is only in the author's report (Round 2); see note 1. |
| 5 Receiver marks sheets received; office still can; nothing broader | Yes | curl rows above; `pack.test.ts:436` |
| 6 Tests cover the above | Yes | 12 new tests; the round-2 tests fail on round-1 code |

## Blocking findings
None for the backend.

## Checks
- [x] Only owned paths changed. `modules/production/**`, `db/schema/production.ts` (the module schema file, per the role), and the granted `db/schema/{orders,tenancy}.ts` and `orders/state-machine.ts`. Also one line in `modules/orders/service.ts:160` (`toOrder` maps `packOverride`), outside the grants. It's the unavoidable same-day consumer fix for the stub's required field, and the report says the tech lead named it. Not blocking.
- [x] Nothing outside scope. The new table `floor_requests` wasn't in the grants, but AC 1's replay needs storage, and backend-foundation co-reviews it (approved).
- [x] Tests exercise the behavior, and none were weakened. Round 2 changed the round-1 assertions (`ready_to_ship` → `in_production`) to follow decision 0010. That's a deliberate spec change, not a loosening.
- [x] Tenancy: `withTenant` on the handler; no `withSystem`; `company_id` + RLS + a `company_id`-leading index; cross-tenant `NOT_FOUND` tested (`pack.test.ts:291`). Idempotency: key `(company_id, kind, idempotency_key)`, stored result, `CONFLICT` on mismatch. No money. The floor messages are server strings, like the existing scan messages.
- [x] Decisions recorded: 0010. It's still untracked in `invai-docs` (`?? decisions/0010-pack-hand-to-lead.md`), so the tech lead should commit it with the wave records.

## Optional notes (not blocking)
1. The AC 4 amendment (state-based idempotency accepted, explicit keys deferred to B-27) exists only in the author's report. Record it in the card or in `wave.md`, and keep B-27 open.
2. `db/schema/orders.ts:104-105` still says "packed with units missing". It should say "handed to a lead" (same stale wording as the contract).
3. The hand-off result is stored under its key, so a later "Mark packed" must use a **new** key; the same key gets `CONFLICT`. T-4-4 should mint one key per tap intent, not one per order.
4. Today's pack count can exceed the unit count. See `T-4-1-qa-engineer-r1.md`: this is existing behavior, not caused by this card.
