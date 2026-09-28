---
name: digest-gate-flow
description: How to get a real weekly digest + email on the fresh seed at a gate (sweep timing, opt-in order, token from the email, undo shape) without touching product code.
metadata:
  type: project
---

Wave 19 gate, 2026-09-28: the seed shop (America/Phoenix, default slot Mon 07:00) gets its digest from the worker's own hourly `digest.sweep` (`5 * * * *`) at the first :05 after 07:00 local on Monday, so a gate run on a Monday morning needs no forced build: seed → opt `owner@` in (`me.notifications.set {kind:"digest", on:true}`) → start the worker → the sweep builds `2026-W<n>` and `digest.ready` → `digest.deliver` emails Mailpit within a second. On another weekday, enqueue `digest.build {companyId, weekKey}` (jobs.ts `buildJob`) or call `buildDigest(companyId, weekKey, at)` with `at` = Monday 07:05 local.

**Why:** delivery runs once per digest; if the owner opts in after the build the email is skipped (`opted_out`) and only `sendPreview` can send.

**How to apply:** take the unsubscribe token from the email's `List-Unsubscribe` header (or the "Unsubscribe with one click" line) and pass it as `E2E_DIGEST_UNSUB_TOKEN` to `pnpm e2e`; POST `/l/:token` with form `List-Unsubscribe=One-Click` unsubscribes (idempotent, same `updatedAt`), POST JSON `{"undo":true}` restores (409 `not_unsubscribed` when nothing to undo), GET only 302s to `/unsubscribe?token=` (tampered → `?error=invalid`). `digest.get` numbers equal `finance.profit` for the same Phoenix week only until the golden path imports fixture orders dated inside that week (order 3310000004, $26.99 / $7.96 net).
