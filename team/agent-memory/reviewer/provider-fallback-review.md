---
name: provider-fallback-review
description: When a client method "never throws" and synthesizes a fallback (placeholder/mock), check which errors trigger it and whether the fallback is ever replaced
metadata:
  type: feedback
---
2026-09-30 T-P1-4: `imaging.preview` fell back to a gray placeholder on ANY error (422, 5xx, timeout), and the job stored it as the real preview_key with no re-render path. Card AC asked for a mock "when imaging is down", so noted non-blocking.

**Why:** a catch-all fallback turns transient outages into permanent wrong data silently.
**How to apply:** for any "never fails" provider wrapper, list the error classes caught, and check whether there's a recovery (re-run on recover, isUp skip like catalog QA job). Also check UI fallbacks (web order-detail falls back to design preview) before judging seed/data gaps as user-visible.
