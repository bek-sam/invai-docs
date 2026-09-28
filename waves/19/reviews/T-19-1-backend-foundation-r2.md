# Review of T-19-1 (round 2)

- Reviewer: backend-foundation on Sonnet 5
- Author: architect on fable
- Verdict: approve

Scope of this round: verify the round-1 blocking finding (README.md / ADR 0016 self-contradiction on
whether `GET /l/:token` mutates) is fixed, per the tech lead's pointer to commits `83eee25`
(invai-contracts) and `9a1a31a` (invai-docs), and the "Link-route rule, clarified" entry in
`invai-docs/waves/19/wave.md`. I did not re-open the rest of round 1 (already approved there in
substance; only this one finding was blocking).

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 83eee25` | README.md reworded: "`GET /l/:token`: never changes a person's email preference or unsubscribe state — only `POST` with `k: unsubscribe` does that", with `k: click` described as "performs exactly one write: it records the click idempotently (first click wins, a repeat is a no-op...) ... purely for the `digest_action_click_rate` metric", plus a stated rationale (RFC 8058 / link-scanner safety is about not letting an automated GET unsubscribe someone, not about GET never writing). Also adds a `superRefine` to `DigestFact` in `src/schemas/digest.ts` rejecting a non-integer `value` when `unit === "cents"`, with new assertions in `src/digest.test.ts` |
| `git -C invai-docs show 9a1a31a` | ADR `0016-signed-link-routes-and-notification-preferences.md` point 3 reworded with the identical narrowing ("never changes a person's email preference or unsubscribe state... only POST... does"), same click-write description and same RFC 8058 rationale; `Status:` line untouched (still accepted) — matches the commit message's claim that this clarifies wording, not the decision |
| `invai-docs/waves/19/wave.md:63-64` ("Link-route rule, clarified") | States the same resolution: GET never changes preference/unsubscribe state, click GET records idempotently, README and ADR aligned — consistent with both diffs |
| `cd invai-contracts && pnpm typecheck` | `tsc --noEmit` clean |
| `cd invai-contracts && pnpm lint` | biome: "Checked 55 files. No fixes applied." |
| `cd invai-contracts && pnpm test` | `Test Files 7 passed (7)`, `Tests 68 passed (68)` |
| `git -C invai-contracts status --short` | clean; working tree matches `83eee25` |
| `git -C invai-docs status --short` | clean; working tree matches `9a1a31a` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 6 (README pins `/l/:token` shape, consistently) | yes | README and ADR now say the same thing: GET never touches preference/unsubscribe state; the `click` GET's one write (idempotent click record) is named and justified, not hidden under "never mutates" |

## Blocking findings
None. Round-1 finding 1 is resolved: the wording no longer licenses two readings. An implementer
building T-19-4 now has one consistent rule (don't let GET unsubscribe; GET click-recording is an
intentional, idempotent, named exception) instead of a sentence that said "never mutates" and then
described a mutation in the same breath.

## Checks
- [x] Only owned paths changed — `invai-contracts` diff touches `README.md`, `src/digest.test.ts`,
  `src/schemas/digest.ts` (architect's own paths); `invai-docs` diff touches
  `decisions/0016-signed-link-routes-and-notification-preferences.md` only
- [x] Nothing outside scope — this round is exactly the round-1 fix plus the small optional
  cents-integer check on `DigestFact.value` I'd noted as optional (not required, but harmless and
  tested)
- [x] Tests exercise the behavior, none weakened — new assertions added to an existing `it` block in
  `digest.test.ts` (cents fact must be a whole number; non-cents units unaffected); test file count
  and pass count unchanged (68/68) because these are new expectations inside an existing test, not a
  loosening
- [x] Tenancy / idempotency / money / en-es — N/A beyond round 1; the reworded prose itself now
  correctly names the click-record write as idempotent (matches `digest.recordClick` semantics
  already reviewed in round 1)
- [x] Decisions recorded where needed — ADR 0016 updated in the same round, status unchanged
  (accepted), which is correct: this is a wording clarification of an already-accepted decision, not
  a new decision or a reopening

## Optional notes (not blocking)
- None new this round.
