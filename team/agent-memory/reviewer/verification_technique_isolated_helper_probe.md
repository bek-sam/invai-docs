---
name: verification-technique-isolated-helper-probe
description: How to prove an e2e helper (e.g. settled()) really throws on timeout without starting the dev stack
metadata:
  type: feedback
---

For a pure e2e helper function (no app server needed), don't just read the diff or trust the
author's report for "it throws on timeout" claims — reproduce it directly: symlink the repo's
`node_modules` into `/tmp/<scratch>`, copy just the helper file(s) plus a minimal
`playwright.config.ts` and one probe spec that uses `page.setContent(...)` (no `page.goto`, no
dev server) to force the timeout/non-timeout branches, then run
`node_modules/.bin/playwright test`. Delete the scratch dir after.

Why: task cards for this kind of fix often say "don't start a stack" for the E2E suite itself,
but that doesn't prevent isolating the one function under test with a fake DOM — it's cheap,
fast (a few seconds), and catches cases where `expect(...).toPass()` either doesn't rethrow the
last error or silently swallows it, which a pure diff read or a green full-suite run wouldn't
distinguish from the old `.catch(() => {})` behavior (the suite would also look green if the
helper still swallowed failures, since nothing in it was *testing* the swallowing).

How to apply: use this whenever a card changes a shared test helper's failure/retry semantics
(polling, toPass, custom matchers) and the acceptance criterion is "it fails loudly instead of
swallowing." Also check the installed Playwright version's `toPass` type doc in
`node_modules/.pnpm/playwright@<version>/node_modules/playwright/types/test.d.ts` to confirm
`toPass` only paces the callback's retries (its own `intervals`), not hidden auto-retries of
assertions/actions nested inside it — a callback with a plain `locator.count()` (no nested
`expect(locator)...` assertion) avoids that trap.
