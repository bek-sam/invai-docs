---
name: rate-bucket-review-checks
description: How to review rate-limit bucket classification changes (bucketFor / NON_GET_READS, T-P3-1) and probe tb:* keys live
metadata:
  type: reference
---
- All read permissions in invai-contracts/src/roles.ts end in `.read`, so a `/\.read$/` filter over listProcedures is complete (re-check if PERMISSIONS grows).
- Mutation-test the pin in a /tmp git-archive copy: drop one STAYS_WRITES entry, then put one path in both lists. Both must fail.
- Live probe: owner cookie sign-in (POST /api/auth/sign-in/email with an Origin header), then hit POST /api/v1/files/download-url in a loop and check `tb:reads:<companyId>` / `tb:writes:<companyId>` with `docker exec local-valkey-1 valkey-cli -n <db>` (no host redis-cli).
- Drain a bucket with `HSET tb:<b>:<co> tokens 0 ts <future>`; expect 429 RATE_LIMITED + retry-after.
- seed-output.json's stationToken can be stale against the dev DB (401). Use an owner session: buckets are per company.
- Watch for ignored inputs like skuRules.suggest `useAi` that could later make a "read" costly.
