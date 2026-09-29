# Scope check: business-analytics-v2 (A1/A2) — product-manager, 2026-09-28

Source: `specs/business-analytics-v2.md`, backlog rows B-168..B-183, `product/scope.md` items 5–8, 13, 14, 17
and fences, `owner-inbox.md` OI-18 (open).

| Row | Scope item or status | Note |
|---|---|---|
| B-168 | item 8, supports 5/6 | Seed/test infra, not a new product surface. No fence issue. |
| B-169 | item 8, supports 5/6/7/13 | Read-only contract for existing scope items' data. No fence issue. |
| B-170 | item 8 (Profit per order, design, blank and channel) | CM ladder, leakage, shipping margin, bridge, break-even are all profit views. Fits. |
| B-171 | item 5 (production floor), item 7 (shipping) | `dest_zone` stores a carrier zone (1–9) only, no address/ZIP — passes the buyer-PII fence. Confirm AC-A4's column-list test lands with the card. |
| B-172 | item 6 (blank inventory, reservations, POs, receiving, reorder) | Size-split is a suggestion the shop edits before submitting (AC-C3) — passes the "no automatic changes" fence. |
| B-173 | item 8 | Web surface for B-170. Fits. |
| B-174 | item 5, item 6 | Web surface for B-171/B-172. Fits. |
| B-175 | item 13 (AI business assistant, read-only tools) | Five new read-only tools, no write capability, no new PII surface. Fits. |
| B-176 | item 17 (weekly digest) | New detectors D9–D13, same suggest-only pattern as existing detectors. Fits. |
| B-177 | item 14 (Today command center) | Same detector code as the digest, ranked suggestions with $ impact, no auto-action. Fits. |
| B-178 | **needs SCR** | New surface (goals/targets), not in items 5–8/13/14/17. Correctly deferred to Track D/A3; gated on owner OI-18 option A. |
| B-179 | **needs SCR** | Not in current scope items; also needs ≥8 weeks of live-shop history it doesn't have yet. Gated on OI-18 option B. |
| B-180 | **needs SCR** | Buyer PII (keyed id) — the fence is "no buyer PII in analytics"; this is the one row that would touch it if approved. Correctly gated on OI-18 option C + compliance-officer review; Amazon excluded per Amazon data rules, Etsy needs counsel's read of the "no analytics" clause first. |
| B-181 | **needs SCR** (separate gate) | Blocked on OI-12/13/14 (email provider/address/CAN-SPAM), not on OI-18. Keep it off both A1/A2 and the A3 list; it moves only when those three are answered. |
| B-182 | tooling, no scope item | Internal move of SQL files to backend scripts, gated on B-49's grant ending. Not a product feature; no PM scope decision needed, just sequencing after B-49. |
| B-183 | **always-in-scope bug (verify first)** | See below. |

## B-183 (Amazon CSV shows $0 shipping on every order)

This is a bug-or-not question, not a scope question. `orders.shipping_cents = 0` on every Amazon order two
things could be true: (a) InvAI's Amazon CSV parser is dropping a shipping/gift-wrap credit column that's
actually in the export — a parsing bug in the shipped CSV-import feature (scope item 2) — or (b) Amazon's
settlement export genuinely carries no separate shipping line for these orders and $0 is correct. The row is
marked "open (verify)" and the owner is integrations-engineer, which is the right first step: confirm against
a real Amazon export column list before calling it a bug.

If verification shows (a), it's a bug in a shipped feature — **always in scope** per `scope.md` "Always in
scope", fix it now regardless of the analytics-v2 wave, independent of this SCR/OI-18 gate. If it shows (b),
it's expected behavior and `shipping_margin.md`'s caveat (already noted in the spec) stands as the fix — no
scope change either way, since it only changes what a definition's caveat says, not what's built.

## Fence check (waves A1/A2 only)

- No cross-seller data: none of B-168..B-177 reads or aggregates another shop's data. Clear.
- No forecasting model: break-even (B-170) and press-time suggestions (B-171) are descriptive/measured, not
  projected; `decisions/0006-v1-cuts.md` stands. Clear.
- No automatic changes: reorder size-split (B-172), Today actions (B-177) and digest detectors (B-176) all
  suggest; the shop acts. Clear.
- No buyer PII in analytics: B-171's `dest_zone` is a zone number, not an address — clear, contingent on
  AC-A4's test actually landing. The one row that would touch buyer PII, B-180, is correctly held out of A1/A2.
- Amazon data rules: no Amazon buyer data is read in A1/A2. B-183 touches Amazon order-level shipping cost
  data only, not buyer PII.

## Spec status

`business-analytics-v2.md` currently reads `Status: draft for product-manager review.` It should **not** move
to `ready` yet: the file has no review log, and `write-spec` requires product-designer (flow), qa-engineer
(testability) and customer-success (evidence) reviews logged in the spec before handoff. None of the five
open questions blocks A1/A2 specifically (Q1 is this confirmation; Q2–Q5 gate Track D items or have a stated
default), so those three reviews are the only thing missing before status can become `ready` for A1/A2.

## Verdict

B-168 through B-177 (waves A1 and A2) fit inside existing scope items 5, 6, 7, 8, 13, 14 and 17 with no fence
violations — the tech lead can plan them once the spec's three outstanding reviews (product-designer,
qa-engineer, customer-success) are logged and status is set to `ready`. B-178, B-179, B-180 and B-181 stay out
of A1/A2, correctly routed to Track D/A3 behind OI-18 (B-181 additionally behind OI-12/13/14) — do not plan
them until the owner answers. B-183 is a verify-first item on a shipped feature: if confirmed as a parser bug
it is always in scope and should not wait for any analytics wave; if not a bug, only its metric-definition
caveat needs a one-line update.
