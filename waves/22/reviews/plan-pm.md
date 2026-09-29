# Wave 22 plan review — product-manager

**Verdict: approve with changes**

## Checked
- 5 cards, ≤5 limit met.
- B-36 (SanMar) correctly called out as staying out of scope (`scope.md` "MVP: out") and no card touches it.
- Every other source is in scope: items 1, 2, 5, 6, 7, 9, 10 (`scope.md#mvp-in`), plus `always-in-scope: bug` (B-183, B-164, B-167), `security` (B-30/S-26), `reliability` (B-163, B-166, B-37 indexes), `pii`/`payments` flags on T-22-3. No fence crossed — this wave doesn't touch legal text, deploys, or market/digest fences.
- Evidence is real and traceable: every backlog id in the sources line exists in `waves/backlog.md` with a matching status ("open (P2 sweep)" or similar) and a source citation (review findings, wave reports).
- Priorities are sensible: these are P2 correctness/idempotency/tenancy items that close gaps in already-shipped MVP scope items (roadmap criterion 1: "no partial items") and enforce owner rules 7–8 (tenant FKs, idempotent webhooks/side effects) — a reasonable use of this slot.
- Contract-first order is right: T-22-1 lands first with additive-only changes and stub procedures, matching the change-order rule (contracts → backend).

## Required changes
1. **T-22-1's scope ref is off.** It lists `product/scope.md#mvp-in` items 1, 4, 5, 6, 7, 9, 10, but its acceptance criteria are shipping (7), production QC/maintenance (5), inventory bins (6), vendor resend (9), org settings, and the TikTok fee + listing attributes (finance/AI listings). Item 4 (Gang Sheet Builder) isn't touched by anything in this card — drop it. Item 8 (profit) is missing even though AC6 adds the TikTok 6% fee constant that T-22-5 then uses for profit math — add it. (T-22-5's own scope ref already correctly includes item 8; only T-22-1's needs the fix.)
