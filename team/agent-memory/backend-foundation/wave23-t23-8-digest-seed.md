---
name: wave23-t23-8-digest-seed
description: T-23-8 (B-207) — building the demo digest at seed time surfaced a hidden dependency on the async finance.recompute job, plus two E2E harness gaps to route around next time.
metadata:
  type: project
---

Card: T-23-8, seed builds `owner@desertbloom.test`'s weekly digest via the real `buildDigest`
(`src/db/seed/weekly-digest.ts`), so a fresh seed already has one for the gate's digest specs.

- **`profit_lines` is job-populated, not seed-populated.** `finance.recompute` only runs from outbox
  events a *worker* drains, which happens after `pnpm db:seed` exits in the normal flow — so
  anything built at seed time that reads `getProfit`/`profit_lines` (the digest's margin/on-time
  deltas) sees an empty table and gets `null` changes, forever (digest builds are idempotent, never
  rebuilt). Fix: call `recomputeProfit(tx, {companyId}, {})` — the same function the nightly job
  calls — synchronously before anything at seed time needs profit data. Caught by actually running
  `digest-dates.spec.ts` AC2 against a real seed, not by reading the code.
- **`invai-web/e2e/helpers/api.ts`'s `seedOutput()` hardcodes `invai-backend/seed-output.json`**,
  no env override. Running `api-golden-path.spec.ts` against a scratch-seeded DB (via
  `SEED_OUTPUT_FILE`, as `team/agent-brief.md` requires) makes test 8 ("floor…") fail with `Station
  token required` and the rest of that serial file skip. Not fixable from `invai-backend` paths;
  filed to QA. Workaround used: verify tests 1–7 through the real suite, verify 8+ independently
  (direct DB read of `stations`, module test suites) rather than faking the file.
- **`invai-web`'s dev-mode Vite CSP hardcodes `connect-src` to `http://localhost:3000`**
  (`vite.config.ts` `DEV_API_ORIGIN`), so `pnpm dev --port <n>` against a non-default backend port
  (e.g. the card's assigned `:3138`) silently fails every fetch — browser shows "can't connect", not
  a CORS or network error, so it's easy to misdiagnose as a backend problem. `prodCsp` (used by
  `pnpm build && pnpm preview`) derives `connect-src` from `VITE_API_URL` correctly — use build+preview
  instead of `dev` whenever verifying against a non-3000 API port.
