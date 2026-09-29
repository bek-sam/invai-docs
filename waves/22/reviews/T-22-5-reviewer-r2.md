# Review of T-22-5 (round 2)

- Reviewer: reviewer on opus. Author: backend-engineer on opus. Verdict: **approve**. Scope: backend `04e72a0` only (fix for r1 finding 1 + note 1); tree clean at HEAD.

| Command (own DB `invai_t22_5r2`, Redis 10; DB dropped, Redis 10 flushed, scratch removed) | Result |
|---|---|
| `pnpm typecheck && pnpm lint` | tsc clean; biome 417 files, no fixes |
| `vitest run --reporter=dot src/modules/vendors src/modules/orders` | 10 files, 67 passed |
| new `delivery.test.ts` on `b90157c`'s `delivery.ts` | 3 of 10 fail for the right reasons: no `unknown` alert, row already claimed when links hang, no `failed` alert |
| `import-races.test.ts` with `pg_advisory_xact_lock` removed, 3 runs | 3/3: the new same-connection quantity-edit test fails (5 others pass) |
| test-weakening scan `b90157c..04e72a0` | no deleted lines; the new `vi.mock("../production/service")` is a dependency (`sheetDownloadUrls`), not the unit |

- Late claim: `delivery.ts` builds the links with no claim, then re-locks and claims `pending -> sending` right before SMTP. A death before that leaves `pending`, and the retry sends 1 email with 0 alerts (test). An in-flight stale claim still goes `unknown` with no auto-resend, which the architect approved.
- One alert per row: every `-> unknown`/`failed` runs under a status-guarded update (`endAttempt`) or the `FOR UPDATE` stale path. The dedupe key is `vendor-sheet-delivery-<id>`. A replayed stale claim still gives 1 alert, and transient refusals give 0. Superseded/cancelled rows don't alert (nothing was lost). The resend 429 is intact (test green), and a `failed` row doesn't start the window.
- Interim alert kind `tracking_push_failed`: **acceptable, not blocking.** The email is no longer lost silently. The alert opens once, the Today sweep doesn't resolve it, it links to the sheet, and in English it shows the specific title and message ("Sheet X: the email to Y didn't go out"). Only the kind headline is wrong. Keep the wave-23 `vendor_email_failed` follow-up.

## Optional notes (not blocking)
1. In Spanish the web shows `a.title` only, and that title is English (`index.tsx:405`). `titleEs`/`messageEs` in `data` aren't read yet: fold this into the wave-23 follow-up.
2. Portal-delivery rows that end `unknown`/`failed` also get "the email ... didn't go out" wording.
3. The r1 notes 1–3 known gaps stand as the report lists them.
