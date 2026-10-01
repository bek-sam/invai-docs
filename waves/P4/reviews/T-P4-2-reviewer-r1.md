# Review of T-P4-2 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: floor-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-floor, HEAD 0b98f85, clean tree) | tsc clean; biome 82 files no fixes; 112/112 passed |
| `scan-test-weakening.sh invai-floor 0b98f85~1` | no hits, no untracked tests |
| `git show --stat 0b98f85` | only `src/components/SyncStatus.tsx`, `src/i18n/es.ts` (owned) |
| `grep -rn "sync-pending\|sync-parked\|sincronizar" e2e src` | only e2e/offline.spec.ts:78,92 assert the English copy, unchanged; no assertion touched |
| Looked at all 10 screenshots in `/tmp/p4-floor/` | es pills on one line with room to spare (02-es: about 25 px free right of the pills); en unchanged; QC "APROBADO"/"RECHAZADO" with order no.; busy OK amber sub-line; wrong blank stays red BLOQUEADO |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | No | Fits on one line (01/02-es), but the copy misleads and drops the meaning of the English (finding 1) |
| 2 | Yes | 04-qc-pass-es, 05-qc-fail-es, 04-qc-pass-en: past-tense result plus order no., no wrap or clip |
| 3 | Yes | 06-busy-ok-es, 07-busy-wrong-blocked-es: no clipped button text or raw key; BLOCKED stays red |
| 4 | Yes | 112/112 unmodified; diff is copy plus `shrink-0 whitespace-nowrap` only; no outbox/sync file touched |

## Blocking findings
1. `invai-floor/src/i18n/es.ts:48-49`: "{{count}} por enviar" drops the noun "escaneos". In this product "enviar" means shipping: the glossary maps "ship by" to "enviar antes de", and the same catalog uses "No se empacará ni se enviará" (es.ts:304) for shipping a package. A packer at the pack station, or a presser near the shipping table, who sees "12 por enviar" reads it as "12 orders to ship" and not as "12 of my scans are still on this tablet". Those scans are lost if the station is forgotten, so this is the warning they most need to understand. The English says "12 scans waiting to sync", so the meaning no longer matches, which fails AC1's "unchanged in meaning".
   Fix (one line, glossary words, matches the "Sin enviar" sheet the pill opens): `pending_one: "{{count}} escaneo sin enviar"`, `pending_other: "{{count}} escaneos sin enviar"`. "12 escaneos sin enviar" is 22 characters against 24 for the English "12 scans waiting to sync", and the English pills fit next to "2 need a check" in 02-en, so it fits. Add a 1280×800 es screenshot with 12 pending and 2 needing a check.

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (the invai-ui header wrap is correctly reported to product-designer, not edited)
- [x] No test weakened (scan clean; e2e asserts English only; the card doesn't need a new unit test for copy)
- [x] Tenancy/idempotency/money: n/a (copy and CSS only). en/es: both present; the plural keys keep `{{count}}`, and identical `_one`/`_other` forms interpolate correctly (i18next count)
- [x] Decisions: none needed

## Optional notes (not blocking)
- es.ts:70-71 "{{count}} por revisar": the meaning is OK ("need a check"). On the QC station it could be read as "waiting for QC", though. "{{count}} con problema" is an option if the product-designer agrees.
- `whitespace-nowrap` plus `shrink-0`: fine as defence in depth.
