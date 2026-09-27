# Wave 19 plan review — product-manager

**Verdict: approve with 2 minor required changes (non-blocking for start; fix before integration gate).**

Scope ref checked: `product/scope.md#weekly-digest` (item 17), `#market-and-digest-fences`. Spec: `specs/weekly-digest.md` AC1–AC33, status ready. Cards: T-19-1..5 (5 cards, within the ≤5 limit).

## Fences — all present and enforced in cards
- No real email: T-19-4 gates `sendUserEmail` on `DIGEST_EMAIL_ENABLED`, Mailpit only, no provider/domain/DNS touched. OK.
- Shadow-only AI summary: T-19-2 AC2 — mode `on` exists in the enum but nothing in this wave sets it; default stays `shadow`/`off`; mock model only, real-model eval waits for OI-8. OK.
- Opt-in, one-click unsubscribe: T-19-4 AC1 default off; AC5 RFC 8058 headers + idempotent POST/GET split. OK.
- No promotions/upsells: not an explicit acceptance criterion anywhere, but content is constrained to "templates from the spec copy table" (T-19-3 AC7) with no free-text admin field — fence is satisfied by construction. **Required change 1:** add one line to T-19-3 or QA's acceptance tests explicitly asserting rendered digest/email text contains only spec-table strings (belt-and-suspenders; low cost).
- No outside calls: hard-fenced in wave.md; Market watch reads wave 18's stored signals only (T-19-3 read-only on `market/**`, calls its service, doesn't fetch anything itself). OK.
- Recipients by permission not role, plan usage gated on `billing.manage`: T-19-1 AC2, T-19-3 AC9/AC10. OK.

Nothing found outside `scope.md#weekly-digest` — no real provider, no cross-shop benchmarking, no scraping, no price/listing writes.

## AC coverage
All 33 spec ACs have a home.

| AC | Home | AC | Home |
|---|---|---|---|
| 1 | T-19-3 AC3 | 18 | T-19-2 AC2, T-19-3 AC8 |
| 2 | T-19-3 AC2, T-19-4 AC2 | 19 | T-19-2 AC3 |
| 3 | T-19-3 AC2 | 20 | T-19-2 AC4 (eval) |
| 4 | T-19-3 AC2 | 21 | T-19-2 AC5, T-19-3 AC8 |
| 5 | T-19-3 AC2 | 22 | T-19-2 AC6 |
| 6 | T-19-3 AC4 | 23 | T-19-3 AC9, T-19-4 AC1/2, T-19-5 AC3 |
| 7 | T-19-3 AC4 | 24 | T-19-4 AC5, T-19-5 AC6 |
| 8 | T-19-3 AC4 | 25 | T-19-4 AC4 |
| 9 | T-19-3 AC5 | 26 | T-19-4 AC2, T-19-3 AC9 |
| 10 | T-19-3 AC3 | 27 | T-19-3 AC10, T-19-1 AC2 |
| 11 | T-19-3 AC4 | 28 | T-19-3 AC1 |
| 12 | T-19-3 AC5 | 29 | T-19-3 AC12 (budget check) + **QA's separate scale run** (qa-report.md) |
| 13 | T-19-3 AC7, T-19-5 AC7 | 30 | T-19-3 AC10, T-19-5 AC4 |
| 14 | T-19-3 AC6 | 31 | T-19-3 AC6 |
| 15 | T-19-3 AC6 | 32 | T-19-5 AC2 |
| 16 | T-19-3 AC6 | 33 | T-19-5 AC4 |
| 17 | T-19-3 AC6 | | |

No AC with no home. AC29 correctly deferred to QA's scale run rather than a card AC — matches spec's own text ("Proven by a separate QA scale run... reported in `build/qa-report.md`"). **Required change 2:** the wave plan should say explicitly (in wave.md's Integration gate checklist) that this scale run happens and is reported before the gate closes — right now only T-19-3's card mentions it in passing; the gate checklist itself doesn't list it. Add a line to the Integration gate section.

## Other notes
- Evidence and decision trail are in order: OI-7 (build), decision 0014, SCR-002.
- 5 cards, 3–4 builders + QA at once — matches wave-size rule.
- Stub/dependency order (T-19-1 → T-19-2/3/4 parallel → T-19-5) is sound and matches change order (contracts → backend → web).

Both required changes are small documentation additions, not scope or design changes — they don't block agents from starting T-19-1/2/4 today. Fix before the integration gate.
