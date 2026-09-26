# Wave 9 plan review — product manager, round 1

Reviewed against `product/scope.md`, the wave goal in `wave.md`, and the DTF production-practices section of `research/10-marketplace-engineering-rules.md`. Read-only on code; changes applied only to `invai-docs/waves/9/**` (cards + `wave.md`) and this file. No scope-change-request needed — this wave was already in scope (imaging correctness/safety is squarely under "Always in scope: bugs in shipped features" and the shipped Gang Sheet Builder / personalization / DTF vendor portal items in `scope.md`'s MVP list).

## Segment fit check
`scope.md` has pilots targeting **mid** first, with **small** shops needing full self-serve and **large** shops gated behind a passed `scale-test`. Wave 9's five cards map onto that cleanly:
- T-9-1 (real PDF/SVG art) and T-9-2 (scannable labels) are correctness bugs that block every segment equally — a mis-rasterized or unscannable transfer is a QC/reprint cost regardless of shop size. No segment call to make here.
- T-9-3 (>200in sheets) is the one card where segment fit actually drives the decision. Sheets over 200in are a **large-shop, high-volume** case — mid shops (the pilot target) running a 22in-wide roll rarely queue anything close to that length. I agreed with the architect's "cap, not split" call on engineering-effort-vs-RIP-compatibility grounds; from the segment side it's reinforced by the fact that the segment most likely to hit this limit isn't cleared to onboard yet (`scale-test` gate). Shipping the simpler cap now, and revisiting split if a large-shop pilot actually needs continuous >200in runs later, is the right sequencing — don't build for a segment that isn't live.
- T-9-4 (personalization: multi-line, outline, photo) is squarely inside MVP item 12 ("Personalization rendering and checks") and item 4 (Gang Sheet Builder). Photo slots and outline are common storefront asks (photo memorial shirts, dark-shirt outline text) — no scope concern, this is filling out an already-in-scope feature rather than expanding it.
- T-9-5 (limits/auth) is squarely "Always in scope: reliability and observability needed to run pilots safely" plus a straightforward security gap (unauthenticated internal service). No debate.

No card here needs a `scope-change-request` — all five are bug/hardening work against already-scoped features, not new capability.

## Where the cards under-scope their own acceptance criteria
Two ACs, as written, can't actually be delivered by the paths the cards own, which would have caused a builder to either silently expand scope into another repo (against the ownership hard rule) or ship an AC that looks done but isn't:
- **T-9-2 AC2** ("file name includes the sheet id and order numbers") pointed at backend evidence (`sheets.ts`) that isn't in any imaging card's owned files, and would have meant touching a deliberately-opaque S3-key scheme for a naming convenience. Redirected the fix to a `ContentDisposition` filename set entirely from within `invai-imaging` — same user-facing outcome (what CADlink/the vendor sees on save), no backend edit, no security-invariant risk. This is a better fix, not just a scope workaround.
- **T-9-5 AC1** ("the backend client retries") genuinely needs one function in `invai-backend/src/integrations/imaging/client.ts` touched. Rather than let that AC quietly not happen (an agent skips it because it's "not my file") or spin up a 6th card past the wave's 5-card cap, I added it as a single-function grant on the card itself so it's visible and reviewable, not silently dropped.

## Acceptance-criteria clarity (a PM reading these before sign-off should not have to guess)
Flagged in each card and summarized in `wave.md`:
- T-9-1: "visual checksum" — needs a concrete, deterministic assertion or the test is decorative.
- T-9-2: "fails loudly" — needs the actual boundary condition, or a reviewer can't tell if the failure path was ever exercised.
- T-9-3: now concrete (200in / format==pdf) after the cap decision — was previously two ACs, now one, testable outcome.
- T-9-4: two competing shrink floors need a stated precedence rule before "auto-shrink" is a checkable behavior.
- T-9-5: two of the four AC2 bounds don't exist in the code yet (confirmed by reading `main.py`) — the card should say "add the bound" explicitly rather than implying the test alone will surface the gap.

## Bottom line
Approved to build as amended. All five cards stay in scope; the two cross-repo gaps (T-9-2 filename, T-9-5 retry) are resolved without a scope-change-request or a 6th card. Sequencing (T-9-1 solo → T-9-2/T-9-3/T-9-4 parallel → T-9-5 solo) keeps to "3 at once" while respecting the one real interface dependency (`vips.py`'s new `target_dpi` param).
