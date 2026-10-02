---
name: feedback-login-resets-locale-from-session
description: Setting localStorage["invai.lang"] before sign-in doesn't stick for es/dark screenshots; routes/login.tsx overrides it from the session's persisted locale
metadata:
  type: feedback
---

Setting `localStorage["invai.lang"]` (or theme) before logging in and expecting it to hold after
sign-in doesn't work: `src/routes/login.tsx` reads `session.data.user.locale` right after a
successful sign-in and calls `setLang(locale)` unconditionally when it's "en"/"es", overwriting
whatever was in localStorage pre-login.

**Why:** found while screenshotting T-P2-4's es/dark order-timeline views for `verify-and-report`
— a pre-login `localStorage.setItem("invai.lang","es")` + reload produced an all-English page
every time, even though the key name was right ([[project_t_a7_ops_inventory_today]] already notes
the key is `invai.lang`, not `i18nextLng`).

**How to apply:** for a Playwright or ad hoc script that needs es/dark screenshots, log in first,
then use the in-app account-menu toggle (`getByRole("button", {name: /Account|Cuenta/})` →
`getByRole("menuitemradio", {name: "Español"/"Oscuro"})`) to switch language/theme live — this also
calls `authClient.updateUser({locale})`, which persists to the shared dev DB `users.locale` column
for that account, so switch it back to `en` afterward (verify with
`docker exec local-postgres-1 psql -U invai -d invai -c "select locale from users where email=...`)
so the next agent isn't surprised by a Spanish-default login. Theme itself is only in
browser localStorage per the artifact's own window, so no DB cleanup is needed for that part.
