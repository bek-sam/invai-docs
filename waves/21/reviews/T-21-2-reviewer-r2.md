# Review of T-21-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: platform-sre on Sonnet 5
- Verdict: approve

Scope reviewed: invai-docs commit `9d5ac3e` (`ops/incident-response.md`, `ops/access-control.md`,
`waves/21/reports/T-21-2.md`, "Round 2" section). Verified each of my round-1 findings 1-6 and
security-reviewer's finding 1 against the same source files cited in the fix, cold (not trusting the
report's prose).

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show --stat 9d5ac3e` | `ops/access-control.md` (+13/-10), `ops/incident-response.md` (+58/-16), `waves/21/reports/T-21-2.md` (+83). Owned paths plus the report only. |
| `git -C invai-docs diff --stat origin/main -- ops/ waves/21/reports/T-21-2.md` (cumulative r1+r2) | Same three files. Nothing outside `platform-sre`'s owned paths. |
| Finding 1 (Etsy path): `sed -n '70,80p;130,140p' invai-docs/research/10-marketplace-engineering-rules.md` | Line 75 (R14) and line 135 both say "within 24 h to `dpo@etsy.com` and to the seller." `incident-response.md`'s new Etsy row states exactly this and cites both lines. **Fixed.** |
| Finding 2 (BETTER_AUTH_SECRET → floor PINs): `grep -n "FLOOR_TOKEN_SECRET" invai-backend/src/env.ts`; `sed -n '155,163p;208,212p' invai-backend/src/modules/tenancy/floor-auth.ts` | `env.ts:227` `FLOOR_TOKEN_SECRET: raw.FLOOR_TOKEN_SECRET ?? raw.BETTER_AUTH_SECRET`; `floor-auth.ts:162` `hashPin` uses `env.FLOOR_TOKEN_SECRET`; `:211` floor session signing uses the same. The doc's new §6.1 step 3 states this exact chain and adds step 3a for rotating `FLOOR_TOKEN_SECRET` independently. **Fixed.** |
| Finding 3 (mock/Stripe claims): `sed -n '170,205p' invai-backend/src/env.ts`; `sed -n '20,32p' invai-backend/src/modules/billing/stripe-events.ts` | `PRODUCTION_KEYS` (env.ts:174-183) includes `EASYPOST_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SMTP_URL`, `MAIL_FROM`, `IMAGING_SHARED_SECRET`; production throws unless `ALLOW_MOCKS=true` (env.ts:193-199). `stripe-events.ts:30` documents "the event row (unique on the Stripe event id) is inserted in the same transaction"; line 52 the insert, line 68 `eventId: ev.id`. The doc's rewritten §6.1 step 4 and §6.4 step 3 match this exactly, including the `ALLOW_MOCKS=true` non-production-only caveat and B-53/wave-2 citation. **Fixed.** |
| Finding 4 (secret inventory gaps): `grep -n "IMAGING_SHARED_SECRET\|SMTP_URL: secret\|MAIL_FROM: secret" invai-backend/src/env.ts` | `IMAGING_SHARED_SECRET` at env.ts:54 and in `PRODUCTION_KEYS` at :183 (matches the doc's `env.ts:54,182` citation, off-by-one from my own recount of the list but points at the right entry — see optional note); `SMTP_URL`/`MAIL_FROM` at :112-113 exactly as cited. `access-control.md` §5's "Not yet SST-managed" row now lists all three plus a new "optional in SST ≠ safe to leave unset" row, and `incident-response.md` §6.1 gained a step 6 for `IMAGING_SHARED_SECRET`. **Fixed.** |
| Finding 5 (qc_fail_spike / severity / audience): `grep -rn "qc_fail_spike" invai-backend/src` (outside `alerts.ts`); `sed -n '344,353p' invai-backend/src/modules/today/service.ts`; `sed -n '157,165p' invai-backend/src/modules/channels/jobs.ts`; `sed -n '29,37p' invai-backend/src/modules/inventory/jobs.ts` | 0 hits for `qc_fail_spike` outside the contract schema — never raised, as the doc now states. `sync_broken` raised `critical` at `today/service.ts:347` and `warning` at `channels/jobs.ts:160` and `inventory/jobs.ts:32` (doc cites `:348`/`:161`/`:33`, one line off each but the right call sites and right severities). `raiseAlert(tx, companyId, ...)` confirmed per-tenant in all three. The doc now states plainly these reach the shop's own users via `alerts.read`, not InvAI staff, and cites B-75 for the paging gap. **Fixed**, with a 1-line citation drift noted below (non-blocking). |
| Finding 6 (guard-bash.py gap): direct read of `.claude/hooks/guard-bash.py` lines 60-76 | Rule 71 matches `gh repo edit\|delete\|rename\|archive`; rule 72 matches `gh api` only when the URL contains `secrets\|variables\|dispatches\|/keys\|-X DELETE\|--method DELETE`. Neither matches `gh api -X PUT .../branches/main/protection`. Rule 65 matches `sst (deploy\|remove)` only, not `sst secret`. Both gaps are real, exactly as the doc's rewritten §1/§2 rows state. `grep -n "B-189" invai-docs/waves/backlog.md` confirms the row exists, owned by platform-sre + security-reviewer, citing "wave 21 T-21-2 reviewer r1". **Fixed.** |
| security-reviewer finding 1 (receiver has no `production.qc`): `sed -n '175,209p' invai-contracts/src/roles.ts` | `PRESSER` (175-182) and `PACKER` (184-194) both include `production.qc`; `RECEIVER` (196-209) has `production.scan` and `production.receive` but not `production.qc`. `access-control.md` §4 now states this exactly, plus `receiver`'s full extra list (`inventory.read/adjust/count`, `purchasing.read/receive`). **Fixed.** |
| B-185/186/187/188 sanity check (referenced by finding 4's neighbor doc, not part of T-21-2, cross-check only) | not applicable to this card — see T-21-3-reviewer-r2.md |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-docs origin/main` | No test files changed by this commit; hits (if any) are unrelated pre-existing prose false positives, same as round 1. |

No processes started. Shared dev DB untouched.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 (incident-response plan) | Yes | Etsy path, secret-rotation containment (BETTER_AUTH_SECRET/FLOOR_TOKEN_SECRET, provider keys, IMAGING_SHARED_SECRET), Stripe containment and the detection table are all now accurate against the cited source files (see evidence above). |
| 2 (access-control policy) | Yes | Secret storage inventory is complete against `PRODUCTION_KEYS`; the app-roles table matches `roles.ts` exactly for all three floor roles; the guard-hook claims are now honest (policy-only, not enforced, with B-189 filed). |
| 3 (every claim cites a file; owner actions marked) | Yes | Every new or changed line I checked cites a real file, and the two disputed facts I could not resolve (Amazon's Etsy contact address, geo-dispersed backups) are marked `[[OWNER: confirm]]` / `[[OWNER]]` rather than asserted. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`): `ops/access-control.md`, `ops/incident-response.md`, plus the card's own report.
- [x] Nothing outside scope.
- [x] N/A — docs-only card, no tests to weaken; scan-test-weakening clean.
- [x] Tenancy/idempotency/cents/en-es: not applicable (docs). The rewritten alert-audience text is itself a tenancy-adjacent correctness fix (it no longer implies InvAI staff can see per-tenant alerts) and it's accurate.
- [x] Decisions recorded where needed: none needed for a docs fix; B-189 is correctly a backlog row, not a decision record.

## Optional notes (not blocking)
- `access-control.md`'s "Not yet SST-managed" row cites `IMAGING_SHARED_SECRET` at `env.ts:54,182`; the zod field is actually declared at line 54 and appears in `PRODUCTION_KEYS` at line **183** in the currently-checked-out `env.ts` (I count `PRODUCTION_KEYS` starting `export const PRODUCTION_KEYS = [` at line 173, with `IMAGING_SHARED_SECRET` the 9th and last entry at 183). A one-line citation drift, not a factual error — the claim itself (it's in `PRODUCTION_KEYS`) is true.
- `incident-response.md`'s detection table cites `sync_broken` call sites at `today/service.ts:348`, `channels/jobs.ts:161`, `inventory/jobs.ts:33`; the `raiseAlert`/`raise` call actually starts one line earlier at each site (`:347`, `:160`, `:32`) with the `kind:` field one line further in. Same non-blocking drift as above — right site, right severity, off-by-one line number.
- Both drifts are the kind of thing that ages out of sync as the code shifts; worth a habit of citing the `kind:`/field line rather than the call's opening line, since that's what a reader `sed -n` would jump to expecting to see the cited fact immediately.
