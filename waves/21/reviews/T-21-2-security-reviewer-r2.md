# Review of T-21-2 (round 2)

- Reviewer: security-reviewer on Sonnet 5
- Author: platform-sre on Sonnet 5 (round 1) / commit shows Opus 5.5 co-author
- Verdict: approve

## Scope of this round
Commit `9d5ac3e` (`ops/access-control.md`, `ops/incident-response.md`,
`waves/21/reports/T-21-2.md`). My round-1 blocking finding was: `access-control.md:78` claimed all
three floor roles (`presser`/`packer`/`receiver`) share `production.qc`, which is false for
`receiver`.

## Fix verified against `invai-contracts/src/roles.ts`
Read the `PRESSER` (line 175), `PACKER` (185) and `RECEIVER` (197) arrays directly:
- `PRESSER`: `production.scan`, `production.qc` — no floor-specific extras.
- `PACKER`: `production.scan`, `production.qc`, `shipping.read`, `shipping.buy`.
- `RECEIVER`: `production.scan`, `production.receive` (**no** `production.qc`), `inventory.read`,
  `inventory.adjust`, `inventory.count`, `purchasing.read`, `purchasing.receive`.

The new `access-control.md:77-82` text: "all three sharing `production.scan`... Only `presser` and
`packer` also have `production.qc` — `receiver` does not; it gets `production.receive` instead.
`packer` adds `shipping.read`/`shipping.buy`; `receiver` adds
`inventory.read`/`inventory.adjust`/`inventory.count` and `purchasing.read`/`purchasing.receive`."
matches the arrays exactly, permission-for-permission. The cited line range (175-209) is accurate
(`RECEIVER` block runs 197-209, `VENDOR` starts at 211). Finding closed.

## Skim of the rest of round 2 for new inaccurate security claims
Round 2 also answered the primary `reviewer`'s findings (Etsy breach path, `BETTER_AUTH_SECRET`
rotation breaking floor PINs, Stripe/mock claims, secret inventory gaps, `qc_fail_spike`, the
guard-bash gap). These touch security-relevant claims (auth secrets, PII incident clocks, payment
provider state, a security-control gap), so I spot-checked the load-bearing citations directly
against code rather than trusting the report:

| Claim | Cited | Verified |
|---|---|---|
| `FLOOR_TOKEN_SECRET` falls back to `BETTER_AUTH_SECRET` | `env.ts:227` | Exact — `FLOOR_TOKEN_SECRET: raw.FLOOR_TOKEN_SECRET ?? raw.BETTER_AUTH_SECRET` |
| PIN hash / floor session sign off `FLOOR_TOKEN_SECRET` | `floor-auth.ts` `hashPin` line 162, session sign line 211 | Exact — `hashPin` at 161-162 (`hmacHex(env.FLOOR_TOKEN_SECRET, ...)`), session token signed with `env.FLOOR_TOKEN_SECRET` at 211/218 |
| `PRODUCTION_KEYS` includes `IMAGING_SHARED_SECRET`, `SMTP_URL`, `MAIL_FROM`, etc.; production refuses to boot unless `ALLOW_MOCKS=true` | `env.ts:174-199` | Exact — `PRODUCTION_KEYS` array (174+) includes `IMAGING_SHARED_SECRET` (183), `SMTP_URL`/`MAIL_FROM` (181-182); boot check at 193 gates on `!raw.ALLOW_MOCKS` |
| `IMAGING_SHARED_SECRET` at `env.ts:54,182` | — | Exact (schema at 54, `PRODUCTION_KEYS` entry at 183, one line off from cited 182 — immaterial) |
| Stripe live, webhook idempotency on event id | `billing/service.ts`, `stripe-events.ts:30,51-68` | Exact — line 30 comment "unique on the Stripe event id", insert at line 52 uses `stripeEventId: ev.id` |
| `stations.revokeToken`/`issueToken` split, `service.ts:798-810/813-816` | `tenancy/service.ts` | Exact — `issueToken` at 798, `revokeToken` at 813 |
| `stations.issueToken`/`revokeToken` permission `stations.manage`, `tenancy.ts:173,177` | contract | Exact |
| `qc_fail_spike` defined in schema, never raised in code | `alerts.ts`, grep | Confirmed — `qc_fail_spike` exists only as a string literal in `invai-contracts/src/schemas/alerts.ts:17`; no `raiseAlert` call site anywhere in `invai-backend/src` references it |
| Alert raise call sites for `sync_broken` etc. | `worker/sweeps.ts`, `worker/outbox-relay.ts`, `ai/breaker.ts`, `today/service.ts`, `channels/jobs.ts`, `inventory/jobs.ts` | Confirmed present in every named file (line numbers off by 1-2 in a couple of spots — `channels/jobs.ts:161`→actual 159, `inventory/jobs.ts:33`→actual 31 — immaterial drift, not wrong file or wrong claim) |
| `gh repo edit` on guard-bash deny list; `gh api -X PUT .../branches/main/protection` is not | `.claude/hooks/guard-bash.py` | Exact — `gh\s+repo\s+(delete\|edit\|rename\|archive)` is a rule; the `gh api` rule only fires on `secrets\|variables\|dispatches\|/keys\|-X DELETE\|--method DELETE`, none of which match a `-X PUT .../protection` call. Also independently reproduced: my own `grep` command containing the substring `gh repo edit` was blocked by this exact hook mid-review, corroborating the claim it documents |
| `sst secret set` not on guard-bash deny list (only `sst deploy\|remove`) | same file | Exact — line 65 rule is `sst\s+(deploy\|remove)` only |
| B-189 added to backlog, owned platform-sre + security-reviewer | `waves/backlog.md:244` | Exact — row present with that text and owners |

No new inaccurate security claim found in this pass. The Amazon-notice-address discrepancy
(`security@amazon.com` vs `security-incident@amazon.com`) is disclosed honestly as unresolved
(`[[OWNER: confirm]]`), not asserted as fact — correct handling of a genuine source conflict, not a
new finding.

## Checks
- [x] Only owned paths changed (`git show --stat 9d5ac3e`: `ops/access-control.md`,
  `ops/incident-response.md`, `waves/21/reports/T-21-2.md`)
- [x] Round-1 blocking finding (`receiver` lacking `production.qc`) is fixed and matches
  `invai-contracts/src/roles.ts` exactly
- [x] No new factual mismatch introduced by round 2's other edits, spot-checked against the actual
  cited source for every security-relevant claim (auth-secret fallback behavior, PII-incident
  clocks, payment-provider state, the guard-bash security-control gap)

## Optional notes (not blocking)
- The FLOOR_TOKEN_SECRET-fallback finding (new in round 2, in response to the primary reviewer, not
  mine) is a genuinely useful catch for anyone running the incident playbook: rotating
  `BETTER_AUTH_SECRET` without first pinning `FLOOR_TOKEN_SECRET` independently would silently take
  down floor PIN auth for every tenant mid-incident. Good addition.
- B-189 (guard-bash gap on `sst secret set` and the branch-protection `gh api` path) is filed with
  the right owners; it is out of this card's owned paths to fix, correctly left as a backlog row
  rather than attempted here.

## Verdict
**approve.** The blocking finding from round 1 is fixed and verified line-for-line against
`invai-contracts/src/roles.ts`. Round 2's other edits (answering the primary reviewer) introduce no
new inaccurate security claim that I could find on a direct-code spot check of every load-bearing
citation.
