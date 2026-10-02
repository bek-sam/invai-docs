---
name: rate-bucket-review
description: How to review moves between rate-limit buckets (bucketFor in invai-backend/src/api/orpc.ts) and which contract flags are dead
metadata:
  type: project
---

2026-09-30 T-P3-1: `bucketFor` reads its HTTP method from the static contract route, not from the request, so a caller can't steer which bucket it lands in. When a procedure moves to `reads`, check that its handler has no write, enqueue, storage put or outbound/paid call. Also check contract input flags the backend ignores: `skuRules.suggest` has `useAi`, which is not wired today. If it ever gets wired, the procedure must leave `NON_GET_READS`.

**Why:** the rate limiter is a security control. A paid call sitting in the 300/min `reads` bucket would be an abuse path.
**How to apply:** for any future change to `NON_GET_READS` or `AI_CHEAP_READS`, re-read each handler.
