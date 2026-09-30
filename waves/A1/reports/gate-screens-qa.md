# A1 integration gate: screen check (owed from wave 23b, T-23-2)

Fresh gate seed (5377 orders, 18mo history). Floor 1280x800, web 1440px, en+es. Throwaway scripts
at `/tmp/a1-screens/{floor,web}/run.mjs` (uncommitted). Screenshots under `/tmp/a1-screens/`.

| Screen / lang | Issue | Sev | Owner | Evidence |
|---|---|---|---|---|
| Floor QC, es worst | Result banner reuses button key `t("floor.qc.pass")` as headline → shows "APROBAR" (imperative) right above "Aprobado: pedido..." (past tense), self-contradicting. `invai-floor/src/stations/QcStation.tsx:145` | Med | floor-engineer | `floor-es-08-qc-pass.png` |
| Web order drawer timeline, en+es | Raw always-English state string `"transfer_in → pressed"` shown as plain text, redundant with the correctly translated `StatusBadge`s right after. Built at `invai-backend/src/modules/orders/service.ts:639`, rendered `order-detail.tsx:434` | Low-Med | backend-engineer (orders) | `web-es-02-order-drawer.png` |
| Today alerts panel, es | Alert body stays raw English ("Order ... is past its ship-by", "Ship-by was Sep 28...") while the bold title is translated. Built at `invai-backend/src/modules/today/service.ts:321-322` | Low-Med | backend-engineer (today) | `web-es-01-today.png` |
| Today greeting date, es | Date stays English ("Wednesday, September 30"). `toLocaleDateString(undefined,...)` ignores `i18n.language`. This is B-207 reintroduced: `lib/format.ts`'s `dateLocale()` helper exists exactly to fix this (doc comment names B-207) but `routes/_app/index.tsx:51` bypasses it. Candidate for `log-lesson` (grep-ban `toLocaleDateString(undefined`) | Low | web-engineer | `web-es-01-today.png` |

Checked, no issue: "Buyer" name = intentional PII-purge (`"Buyer (data purged)"`, confirmed via
`orders.list`), not a bug. "Transfers" untranslated in es profit table = already-tracked glossary
gap, not re-filed. Film use 78-87% (one sub-80% row = known end-of-batch exception). No NaN,
no `##` order numbers, no truncation/wrapping in es despite longer strings. Gang sheet detail,
profit ($, 31.4% margin), floor BLOCKED/PRESS/pack screens all correct both languages.

Method: seed's "Press 1" token is pinned (`canSwitch=false`), so it can't reach QC/pack; issued a
fresh "any station" token via owner API (same pattern as `press.spec.ts`) to cover all stations in
one run. Real press/QC/pack transitions happened on 2 seed orders (ordinary floor activity, not a
reseed) while backend-foundation ran concurrent read-only SELECTs — no conflict.

Processes: started `pnpm dev:all` (PID 36387, child `concurrently` 36395) — both stopped, ports
3000/5173/5174/8000 confirmed free. Left untouched: agent's API on :3142 (PID 30429). Dev DB: left
as the fresh gate seed, not reset.
