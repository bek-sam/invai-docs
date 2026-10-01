# Plan review (scope): wave P6. Product-manager

Reviewer: product-manager. Scope: scope refs, fences, and whether other agent-doable P1/P2 (non-Low)
backlog items remain beyond B-31, B-208, B-219, B-249.

**Verdict: approve.**

## Scope refs
All four cards correctly claim an always-in-scope class matching `scope.md`'s "Always in scope" bullets.
T-P6-1 (B-219: dev tooling wiped shared Redis queues/seed-output twice) and T-P6-4 (B-249: non-deterministic
seed; B-208: gate-flaky sub-80% sheet, also wedge correctness) are `always-in-scope: bug`. T-P6-2/T-P6-3
(B-31: token in the `/events` URL, revoke doesn't cut access) are `always-in-scope: security` (v1-#4,
S-30, S-G9). This matches my own P5 hand-off ranking (B-31, B-208, B-219) plus B-249, found during P5's own
T-P5-1 build. Nothing builds past `scope.md`; no scope-change-request needed.

## Fences
`invai-infra` stays read-only (T-P6-1 explicitly leaves `gate.sh` unchanged); no deploy, AWS or outbound
send in any card; Track D, OI-17/18 and waves 24/25 untouched; decision 0020 (reprint mix) is named in
T-P6-4's out-of-scope line; no buyer PII; T-P6-2/T-P6-3 strengthen auth (close a revoke gap), they don't
weaken a control. Ownership is clean (no two cards edit the same file) and the dependency order
(T-P6-3 after T-P6-2's commit, T-P6-4 after T-P6-1's commit) is stated. Fences hold.

## Other open agent-doable P1/P2 (non-Low) items after P6
Checked `backlog.md`'s P1 (29-54) and P2 (55-74) tables, the 2026-09-24 full-codebase-audit P1/P2 sections
(92-182), and the 2026-09-28 reconciliation table (208-217) against wave sources, not row text — stale
again in several places: B-98, B-102, B-162, B-163, B-166, B-167 all still read "open"/"planned" but were
built in waves 21-22 per their own reports (`waves/22/reports/T-22-2.md`, `T-22-5.md`;
`waves/21/reports/T-21-5.md`). B-138 and B-142 read "open" but were explicitly moved to wave 25 by
`waves/23b/wave.md:14` ("moved to wave 25 (cap; handoff)"), so they sit behind the decision-0019 pause.
B-108/B-127/B-128/B-129 stay excluded (owner approval / OI-3, OI-8, OI-9, OI-11, OI-12-14).

**Two remain open, agent-doable, excluded by no fence:**
1. **B-134** — shared `ConfidenceBadge`/vote-card component in `invai-ui` was never built. Wave 23b's
   T-23-4 planned it "via a product-designer grant" but that card never started
   (`waves/23b/wave.md:26`: "T-23-3 and T-23-4 not started"), and nothing since references it. Owner:
   product-designer.
2. **B-115** — `guard-bash.py` gaps accepted in wave 16 (Bash edits like `sed -i` untracked by the
   verification gate; runtime-built commands invisible to the guard; AI credit/spend breakers checked once
   per assistant question, not per tool round) have no mention in any wave file or `lessons.md` since
   `waves/17/reviews/T-17-3-security-reviewer-r1.md`. Owner: platform-sre + ai-engineer.

Both are smaller than a full wave slot each; recommend the tech lead fold them into one P7 card (or a slot
each if capacity allows) rather than a status-only file.

## Ranked for a P7 hand-off
1. B-134 — design-system consistency; the digest/market vote-card pattern should live in one place before
   more screens copy the local version.
2. B-115 — tooling/guard hardening; lower shop impact, open longest (since wave 16).
