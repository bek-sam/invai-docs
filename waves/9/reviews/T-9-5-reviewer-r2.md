# Review of T-9-5 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer + platform-sre on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "client.ts:207\|header_height_in" invai-docs/waves/9/wave.md` | line 121: "Grant approved after the fact for T-9-5 backend `client.ts:207,246`: the `header_height_in` type lines for T-9-2 (additive, needed for T-9-2's header strip)." |

No code changed since r1 (`invai-imaging 87e01e0`, `invai-backend 2b98c13`, `invai-contracts 311d357` are the
same commits reviewed in r1); only the grant record changed. r1's evidence (test runs, weakened-test scan,
pre-change replay, full diff read of all three repos) stands and isn't re-run here.

## Acceptance criteria
Unchanged from r1 — all 7 (including the added AC7) verified met; see `T-9-5-reviewer-r1.md`.

## Blocking findings
None. r1's sole blocking finding — the out-of-grant `header_height_in` type lines in
`invai-backend/src/integrations/imaging/client.ts:207,246` — is resolved: the tech lead's
after-the-fact grant is now recorded in `wave.md` line 121, matching the precedent already set
for this card's other outside-grant edits (vips.py, pdf_input.py, conftest.py, test_api.py
fixture, README, .env.example).

## Checks
- [x] Only owned paths changed, now fully covered by grants (owned + two after-the-fact lists)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (r1 evidence)
- [x] Tenancy / idempotency / money / en-es — n/a, confirmed in r1
- [x] Decisions recorded where needed — `wave.md` line 121

## Optional notes (not blocking)
Carried over from r1: RSS/time weren't re-measured before/after (acceptable, no pixel-pipeline
change); pre-existing lint debt on `sheetSpecPdfCapError` (T-9-3) and `app/labels.py` (T-6-2)
correctly not attributed to this card.
