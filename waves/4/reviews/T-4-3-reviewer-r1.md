# Review of T-4-3 (round 1)

- Reviewer: reviewer on Opus
- Author: floor-engineer on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-floor log --oneline` (commits under review) | `04b34d9` (receiving station), `4775ce4` (typecheck-green stub) |
| Setup: worktree `invai-floor-r43-review` at `04b34d9`, `node_modules` symlinked to `invai-floor/node_modules` | ok |
| `./node_modules/.bin/tsc --noEmit -p .` | clean, no errors |
| `./node_modules/.bin/biome check .` | "Checked 68 files in 51ms. No fixes applied." |
| `./node_modules/.bin/vitest run` | 6 test files / 54 tests passed |
| `./node_modules/.bin/vite build` | passed; main chunk 857.04 KB / **260.71 KB gzip** (matches the author's report exactly) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor-r43-review 01ede42` | **no hits**: 0 removed assertions / 45 added, no `.skip`/`.only`, no mocks of the unit under test, no config loosening, no test-only production branches |
| `git -C invai-floor diff --stat 01ede42..04b34d9` | 17 files: only `src/stations/receiving/**` (new), the card's own i18n keys (`en.ts`/`es.ts`, 60 lines each), and exactly the granted lines — `StationShell.tsx` (+12, matches the typecheck-fix grant from `4775ce4` plus the 2-line grant from `04b34d9`), `outbox/db.ts` (+2/-1, the approved `ReceivingCommand` union hunk), `app/actions.ts` (+3, the approved `sendReceiving` hook), `api/demo.ts` (+4/-1, the granted typecheck fix). No out-of-scope files. |
| Live stack: `invai-backend` HEAD (`bdffe6f`, includes T-4-1) on `:3192`, `DATABASE_URL`→`invai_r43_copy` (`createdb -T invai` + `pnpm db:migrate`, reported "up to date"), `REDIS_URL=redis://localhost:6379/10`; floor worktree on `:5192` (`VITE_API_PROXY=http://localhost:3192`) | both healthy (`/health` ok) |
| Created a `receiving`-kind station via the owner API (seed has none), signed in as `receiver@desertbloom.test` PIN `1177` in the browser | login lands straight on the Receiving screen, per T-4-1's `stationKind` wiring |
| PO receipt: created `PO-20260925-01` (12/6/24 line qty) via the owner API and submitted it, partial-received 5 of the S line, then double-clicked "Receive 5 (partial)" | UI showed one RECEIVED screen ("37 still to come" after); `purchase_order_receipts` table has **exactly 1 row** for that submission — the double tap did not double-count |
| Over-receipt: +8 on a line with 7 outstanding | client blocked submit (disabled button, warning banner); direct `curl` to `purchase-orders/{id}/receive` with `qty: 999` independently confirmed the server also refuses with `BAD_REQUEST` ("receiving 999 but only N outstanding") |
| Capped to outstanding, "All arrived", received the rest | `PO-20260925-01 is complete`; DB: status `received`, lines 24/24, 12/12, 6/6, **exactly 2** `purchase_order_receipts` rows total for the whole PO (partial + rest) |
| Vendor transfer: looked up a real `transfers.id` on printed sheet `2026-09-22 #23`, scanned `T:<transferId>` in the dev simulate box, confirmed | sheet `status` → `received`; every non-terminal item on the sheet moved `on_sheet → transfer_in` (verified by SQL against `transfers`/`order_items`) |
| Stock count: scanned `B:<variantId>` for a blank with `on_hand=17`, counted 1, saved | screen showed system 17 / counted 1 / difference **-16**; "1 blank corrected"; call went through `inventory.count` |
| True offline replay: created `PO-20260925-03`, loaded its list online, then pointed the Vite dev proxy at an unreachable port (real network failure, not just `navigator.onLine`), partial-received 3 of 8 | "GUARDADO SIN CONEXIÓN" / "Faltan 5" screen; the local list folded the pending receipt in (showed 3 of 8) while the server had **0** receipt rows for that PO |
| Restored the proxy, waited for the outbox's backoff retry | sync badge cleared, "En línea" restored, list re-fetched to 3 of 8 from the server, and the server now has **exactly 1** receipt row with the same `idempotencyKey` the client generated once — no duplicate from the offline replay |
| Double-tap in Spanish on a second PO (partial receipt of 3) | again exactly 1 receipt row in the DB |
| `curl` a replay of `sheets.markReceived` on an already-received sheet | `409 INVALID_TRANSITION` — matches the author's own documented gap (handled today by the outbox's pre-existing `isAlreadyApplied` heuristic, not new to this card) |
| `grep` for raw English strings in `src/stations/receiving/*.tsx` outside `t(...)` calls | none found |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. PO receiving: pick/scan, count blanks, submit with idempotency key, partial allowed, over-receipt warns | Yes | Live partial+double-tap+over-receipt+complete flow above; `ReceiptDraft.idempotencyKey` made once per draft (`newReceipt`), reused unchanged on `queued`/`sent`, only regenerated after a genuine `failed` rejection |
| 2. Vendor transfers: scan sheet QR or pick from sent/shipped list, mark received | Yes | `ARRIVING_SHEET_STATES = ["printed","shipped"]`; live scan-by-transfer + mark-received above; server enforces the same via `SHEET_TRANSITIONS` (independently verified: a replay on `received` returns `INVALID_TRANSITION`, not silently re-applying) |
| 3. Stock count: count a bin/location, show difference before submit, record via `inventory.count` | Yes | Live count above; `CountInput` sent matches the contract shape exactly (`locationId`, `lines[]`, `note`) |
| 4. Offline: works through the outbox, T-4-2's interface | Yes | Live true-network-failure test above: queued while unreachable, replayed exactly once on reconnect, same `clientish` idempotency key reused (`ReceiptDraft.idempotencyKey`/`OutboxCommand` entry, never regenerated on retry) |
| 5. Quality: en/es, tablet layout, large touch targets, same station-header pattern | Yes | Walked both languages at 1280×800; `StationHeader` from `@invai/ui` reused unmodified; `Stepper` buttons are `size-16` (64 px); no raw English found in the new files |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` above matches owned paths + the three named grants exactly)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan: 0 hits; new `logic.test.ts` covers PO matching, idempotency-key-per-draft, over-receipt cap, sheet lookup, count variance, and the demo backend's replay/refusal rules)
- [x] Idempotency: PO receiving has a client + server key, verified live under a real dropped connection with zero duplication; sheet/count writes still rely on the pre-existing (not new) `isAlreadyApplied`/absolute-overwrite behavior — see the inventory co-review for the severity judgment on that gap, which is outside this card's owned paths to fix
- [x] en/es text complete; money not applicable here (unit counts only, no cents)
- [x] Decisions recorded where needed — none new; the over-receipt "warn" vs. "block" choice is explained and consistent with the server's own refusal

## Optional notes (not blocking)
- The main JS chunk grew from 250.87 KB to 260.71 KB gzip (+9.8 KB); it was already over the 150 KB budget before this card. Lazy-loading `ReceivingStation` (flagged by the author, needs a `StationShell.tsx` change outside the 2-line grant) is a reasonable T-4-4 follow-up.
- On a cold reload, the very first vendor-transfer scan can briefly miss if it lands before the transfer index for the printed/shipped sheets has finished its first async fetch (observed once in manual testing, self-corrected on the next scan). Worth a quick look if it recurs, but I could not reliably reproduce it as a real defect distinct from test-harness timing.
