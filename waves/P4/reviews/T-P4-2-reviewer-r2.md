# Review of T-P4-2 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: floor-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-floor, HEAD b2cfd13, clean tree) | tsc clean; biome clean; 13 files, 112/112 passed |
| `scan-test-weakening.sh invai-floor 0b98f85~1` (covers both commits) | no hits, no untracked tests |
| `git show --stat b2cfd13` | only `src/i18n/es.ts` (owned); 13+/4-, copy and comments only |
| `grep pending_/parked_ src/i18n/{en,es}.ts` | es `pending_one` "{{count}} escaneo sin enviar", `pending_other` "{{count}} escaneos sin enviar"; `{{count}}` kept in both |
| Looked at `/tmp/p4-floor/r2-01-header-pending1-es.png`, `r2-02-header-pending12-review2-es.png` | "1 escaneo sin enviar" (singular) and "12 escaneos sin enviar" + "2 por revisar" (plural), one line each, no clip or raw key; the header still has room at 1280×800 |

## Round 1 finding
1. es.ts:48-49 "por enviar" dropped the noun and read as shipping: **resolved**. The text is now the one I proposed, it matches the catalog's own `outbox.title` "Sin enviar", and the screenshots show the `_one`/`_other` forms interpolate with the right noun for 1 and 12.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | r2-01 / r2-02: all three pill texts on one line at 1280×800 es; meaning matches the English "N scan(s) waiting to sync" again |
| 2 | Yes | Unchanged since r1 (04-qc-pass-es, 05-qc-fail-es) |
| 3 | Yes | Unchanged since r1 (06-busy-ok-es, 07-busy-wrong-blocked-es) |
| 4 | Yes | 112/112 with no test file changed; no outbox/sync file touched in either commit |

## Blocking findings
None.

## "por revisar" reasoning
Acceptable. That r1 note was optional. "revisar" is the generic word for the English "need a check", and QC uses "control de calidad". It fits next to the pending pill (r2-02). Leaving it is fine. The product-designer co-review can still ask for "con problema".

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] No test weakened (scan clean; e2e asserts English copy only, unchanged)
- [x] Tenancy/idempotency/money: n/a (copy only). en and es both present, placeholders kept
- [x] Decisions: none needed

## Optional notes (not blocking)
- The es.ts comment block for `pending_*` (5 lines) and `parked_*` is long for a catalog file. Trim it on a later pass.
