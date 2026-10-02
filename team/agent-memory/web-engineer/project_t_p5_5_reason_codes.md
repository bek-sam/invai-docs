---
name: project-t-p5-5-reason-codes
description: T-P5-5 patterns — testing a route file's pure helpers, and finding seeded orders with a real reasonCode/messageCode to screenshot
metadata:
  type: project
---

Built on `Alert.messageCode`/`params` and `TimelineEntry.reasonCode`/`reasonParams` (contract
0.11.0, architect ruling R1 in `waves/P5/reviews/plan-architect.md`): both map a code to a
translated line through a `Partial<Record<Code, (t, params) => string>>` lookup, never an
exhaustive switch, so a future code this build doesn't know yet degrades to the old fallback
instead of a type error.

**Why:** the rule is explicit in the contract's own doc comments (`AlertMessageCode`,
`TimelineReasonCode` in invai-contracts), not just a style preference — an older web build must
keep working when the backend adds a code.

**How to apply, two reusable techniques:**
1. A route file (`src/routes/_app/**`) can have pure helper functions worth unit-testing even
   though the file itself is a TanStack Router route. A colocated `*.test.ts` builds fine either
   way, but name it with the router plugin's own ignore prefix (`-index.test.ts`, not
   `index.test.ts`) to avoid its "does not export a Route" build warning. Export just the pure
   functions you need to test (e.g. `alertDetail`, `alertDateLabel`), not the whole module.
2. To find a seeded order that actually exercises a given `reasonCode` (not every order has one —
   plain shipped/delivered transitions usually don't), use the Orders page's `?view=` search param
   (`needs_mapping`, `blocked`, `needs_artwork`, `on_hold`) instead of scanning the default "All"
   list; `blocked`/`needs_mapping` reliably turn up `on_sheet`/`sheet_received`/`mapped` reasons
   from the seed's recent activity.

**Round 2 (reviewer finding):** `p.someName ?? ""` is not a safe default for every param — when the
backend deliberately omits a key (not just sends an empty string) because the real value is unknown
(e.g. `vendors/delivery.ts:242` omits `vendorName` for an unidentified vendor), the templated line
gets a visible gap ("the email to  was sent"). For a name-shaped param, branch on presence and add a
vendorless sentence variant (en+es, same tone) instead of defaulting to "". A 0-default is fine for
counts; it's only name/identifier-shaped params that can leave a hole.
