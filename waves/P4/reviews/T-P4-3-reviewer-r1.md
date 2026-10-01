# Review of T-P4-3 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-web, HEAD 85c4ed0, clean tree) | tsc clean; biome 197 files, 1 pre-existing warning (markdown.test.ts, not this diff); 21 files, 136/136 passed |
| `scan-test-weakening.sh invai-web 85c4ed0~1` | no hits |
| `git show --stat 85c4ed0` | 5 files: i18n-es.json, en.ts, es.ts, designs.$designId.tsx, billing.tsx: all owned |
| Flattened en.ts/es.ts vs `scripts/i18n-es.json` (node strip-types script) | `action.loadMore` and `billing.ledgerTokensInOut` identical in all three; no en key missing in es; `i18n-es-missing.json` absent. 8 older es/json drifts (assistant.q1-5, listings.highRisk*) predate this card |
| Contract + imaging grep | `QaIssue` = {code (5-enum), severity, message: string}; message is imaging prose rendered at designs.$designId.tsx:445 |
| Looked at es list 1440/390, es detail 1440 (+bottom) / 390-bottom, es billing 1440-bottom, en list 1440 | see findings |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | No | `loadMore` raw-key fix and translated alt are correct (es-design-detail-1440 "sleeve_left" before, -bottom "Manga izquierda" after). But the 390 detail clips the placement (finding 1) |
| 2 | Yes | es-billing-1440-bottom: "1,447 entrada / 2,911 salida", es-US grouping via `localeNumber`; no bare `toLocaleString()` in billing.tsx |
| 3 | Yes | en defaults match en.ts ("Load more", "{{in}} in / {{out}} out"); en-designs-list-1440 unchanged; catalogs hand-synced, no regeneration |

## Blocking findings
1. `invai-web/src/routes/_app/catalog/designs.$designId.tsx:371` (`grid grid-cols-3 gap-3`, holding the placement NativeSelect + width + height). At 390 px in Spanish the placement select shows "Mang ▾" (es-design-detail-390-bottom.png). The author's own screenshot shows it, but the report does not list it. AC1 requires "nothing clipped" at 390 and "each finding is fixed and listed". The failure: an office user on a phone can't tell which placement a file belongs to. "Mang…" could be either sleeve, and the left and right sleeve prints are different files. Fix in the owned file: stack the select on its own row below `sm` (for example `grid-cols-2` with the select `col-span-2`, and `sm:grid-cols-3`). Add a 390 es screenshot.

## Checks
- [x] Only owned paths changed; nothing outside scope (the `loadMore` key also fixes 3 other screens' raw key, a catalog-only change, fine)
- [x] No test weakened; copy-only, no new unit test needed
- [x] Tenancy/idempotency/money: n/a. Money and numbers go through the shared formatter. es in tú form, plain
- [x] `QaIssue.message` routed as blocked to architect + imaging-engineer, not patched: correct per the card ("Backend-sent English … not patched in the web")

## Optional notes (not blocking)
- es.ts:715 `orders30` "{{count}} pedidos · 30 d" has a normal space. At 1440 (es-designs-list-1440) "30" and "d" fall on separate lines, while the English "30d" fits. Use a non-breaking space or "30d". The key also has no `_one` form ("1 pedidos", "1 orders" in en). Worth fixing in the same round.
- QaIssue follow-up: web could map the 5 `code` values to translated generic sentences, falling back to `message`. Give the architect this as option B next to structured params.
- Billing has no "before" screenshot for "in / out"; the diff is self-evident, so this is fine.
