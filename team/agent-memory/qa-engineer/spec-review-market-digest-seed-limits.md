---
name: spec-review-market-digest-seed-limits
description: Demo seed's real limits that block market-signals/weekly-digest style acceptance criteria (history depth, channel status, no sample-workspace type) and how to word ACs around them
metadata:
  type: project
---

Wave 18 (market-signals) / wave 19 (weekly-digest) spec review, 2026-09-27: the demo seed has three limits that made several acceptance criteria untestable as literally written.

1. **Order history is ~30 days**, not years: `ageDays = random.next() * 30` in `invai-backend/src/db/seed/builder.ts`. Any AC needing 26+ weeks of trend, 2-3 years of seasonality, or 156 weeks of own-history cannot run against `pnpm db:seed` output — needs a fixture-built weekly series instead.
2. **Non-Shopify channels are never `"connected"`** in the seed — only `status: "csv_only"` (Etsy, Amazon, TikTok). Only `shopify` is `"connected"`. An AC assuming "Amazon connected" against the seed is false as written; build it via a fixture (`createConnection` with a test override).
3. **"Sample workspace" IS represented, but not by `companies.demo`** (corrected 2026-09-27 by the tech lead): `isSampleWorkspace(companyId)` in `invai-backend/src/modules/tenancy/demo-flag.ts` = `companies.demoOwnerUserId IS NOT NULL` or `settings.demoRetiredAt` set (a user's own demo company from tenancy.demo). The seeded Desert Bloom has `demo = true` and must get real-shop behavior. In a test: `update companies set demo_owner_user_id = <ownerId>` via `withSystem`, then `clearSampleWorkspaceCache()`. No schema change needed; my earlier "no sample-workspace concept" note was wrong.

The seed RNG is deterministic (`rng(20260924)` in `index.ts`), so *shapes* repeat across reseeds, but calendar **dates** are relative to real `Date.now()` at seed-run time. An AC that freezes an absolute date ("Given the seed at Monday 2026-09-28...") is self-contradictory with "the seed" unless the seed was generated under that same frozen clock, which the normal flow doesn't do.

How to apply: when a spec's AC says "given the seed" plus a frozen absolute date, or needs deep history / connected non-Shopify channels / sample workspaces, flag it blocking and propose rewording to "a fixture shop built to <seed shop>'s shape" instead of assuming the seed provides it. Reserve literal "the seed" only for ACs that don't pin a specific calendar date (those are fine for `run-golden-path`-level E2E).
