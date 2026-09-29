# Wave 25 plan review — architect

**Verdict: approve with changes**

Only `wave.md` exists for wave 25 (no individual `T-25-*.md` cards yet). Reviewed at the wave-plan
level, against `.github/workflows/` in each repo and a search for existing OTel usage.

## Checked
- Hard fence held: no deploy, no `gh workflow run`, no secrets/accounts asked of any card; workflows
  are `actionlint`-checked and run only where they need no secret.
- Each of the 8 repos already has its own `ci.yml` (and `invai-infra` has `deploy.yml`, unpinned
  actions, no gate on green CI, no migration step) — T-25-1 (SHA pinning, least `permissions:`,
  scans) and T-25-3 (pinned sibling SHAs gated on CI, migrate task, promotion, smoke, rollback) are
  both real, correctly-scoped gaps against what's actually there, not invented work.
- No existing OTel instrumentation anywhere in the codebase today (checked `invai-backend` and
  `invai-imaging`), so T-25-4 is greenfield, not a rewire.

## Required changes
1. **T-25-4's "OTel traces API → queue → imaging" needs code in a repo backend-foundation doesn't
   own.** `invai-imaging` is a separate Python/FastAPI repo exclusively owned by imaging-engineer
   (`respect-ownership`: an agent doesn't edit another role's repo). A trace that actually reaches
   "imaging" needs a span created inside `invai-imaging/app/main.py`'s request handling, reading the
   incoming `traceparent` header — backend-foundation can propagate the header from the API/worker
   side, but can't complete the chain by itself. T-25-4's card list has no imaging-engineer grant or
   co-reviewer. Add one of: (a) a grant into `invai-imaging/app/**` for the imaging-side span code,
   co-reviewed by imaging-engineer, or (b) scope T-25-4 to "API → queue, with trace-context
   propagated to imaging" only, and open a follow-up card (imaging-engineer, a later wave) for the
   imaging-side spans — state explicitly which, since "→ imaging" in the goal line as written implies
   the chain is complete this wave.

## Notes (non-blocking)
- Same stale-backlog-label note as wave 24; no action needed from me.
