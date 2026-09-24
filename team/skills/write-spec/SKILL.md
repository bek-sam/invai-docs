---
name: write-spec
description: Write a feature spec for InvAI in invai-docs/specs/ with evidence, segments, flow, Given/When/Then acceptance criteria, metrics and open questions. Use when a backlog item is picked for a wave, pilot feedback asks for a feature, or someone says "spec", "PRD" or "acceptance criteria".
---

# Write a spec

Every item the tech lead plans has a spec that QA can turn into tests and a designer can turn into screens,
with no guessing.

## When to use
- The PM picks an item for the next wave (operating system, wave step 1). No spec, no card.
- A pilot issue or scope-change request was approved and needs building.
- A spec exists but its criteria can't be tested (QA or the designer sent it back).

Not for bugs with a clear repro: those get a task card straight from `triage-support-ticket`.

## Steps
1. **Check scope first.** Open `invai-docs/product/scope.md`. If the item isn't in scope, stop and run
   `scope-change-request`.
2. **Read what exists.** Find the screens and procedures the feature touches:
   - Web routes: `ls invai-web/src/routes/_app/**` and `invai-web/src/lib/nav.ts` (screen names).
   - Procedures: `grep -rn "<area>" invai-contracts/src/contract*` and
     `invai-backend/src/modules/<area>/service.ts`.
   - Item states: `invai-contracts/src/states.ts` (`ORDER_ITEM_STATES`, `ITEM_TRANSITIONS`).
   - Logged decisions: `invai-docs/decisions/` (for example `0002-pack-semantics.md`, `0006-v1-cuts.md`).
     Don't contradict one without new evidence.
3. **Gather evidence.** At least one of:
   - a pilot issue id from `invai-docs/customers/issues.md` (created on first use by `triage-support-ticket`),
   - a ranked pain in `research/03-pain-points.md` (quote the number, e.g. "pain #1 late shipment"),
   - a metric from `invai-docs/metrics/weekly/` (created on first use by `weekly-metrics-review`).
   One shop's quirk is not enough; say how many shops have it.
4. **Copy the template.** `cp .claude/skills/write-spec/template.md invai-docs/specs/<slug>.md`. Use a short
   kebab slug that matches the future task card.
5. **Fill each section** (the template lists them). Keep these InvAI rules in mind:
   - **Segments.** State the effect on small (under ~100 orders/day, owner does everything), mid
     (100–1,000/day, 5–30 staff) and large or multi-location shops. Say which one this is for.
   - **Users by role.** Use the real roles: `owner`, `admin`, `office`, `designer`, `presser`, `packer`,
     `receiver`, `vendor` (`invai-contracts/src/roles.ts`).
   - **Floor work.** If a presser, packer or receiver touches it: Spanish copy, 64 px targets, a mismatch must
     block, and it works offline.
   - **Units and money.** Cents, inches, one order item = one physical unit.
   - **Outside approvals.** Name any marketplace or partner dependency (Etsy commercial access, Amazon SP-API,
     TikTok, Walmart, EasyPost) and what works on CSV or the mock until then.
6. **Write acceptance criteria as Given/When/Then.** Each one must be checkable by a test or a curl. Cover:
   - the happy path on the seed shop (Desert Bloom Tees),
   - at least one criterion per state the feature can meet: cancelled after `on_sheet`, `on_hold`,
     `needs_mapping`, `needs_artwork`, a reprint,
   - personalization overflow, a stockout, a marketplace or carrier outage (mock returns an error), a plan
     limit hit (`billing.assertWithinPlan`),
   - scale: a large shop's day (1,000 orders, 5,000 rows in a list),
   - permissions: which role must be refused.
7. **Pick one or two success metrics** from `invai-docs/metrics/definitions/` (created on first use by
   `define-metric`) (late rate, film use %, reprint rate, minutes saved, adoption). If none fits, ask the data-analyst to run `define-metric`. Give the
   baseline and the target.
8. **List open questions** with who answers them: owner, a pilot shop (the owner asks), the architect, or
   compliance.
9. **Get the reviews** named in the operating system: `product-designer` (flow and states), `qa-engineer`
   (testability), and `customer-success` (evidence). Record their verdicts in the spec's review log. Fix
   blocking comments; two rounds, then escalate.
10. **Hand off.** Set status to `ready` and tell the tech lead. Don't assign engineers yourself.

## Rules
- MUST link every claim to evidence (issue id, research section, metric file).
- MUST keep "Out of scope" explicit. Anything not listed in scope is out.
- MUST write user-facing strings in plain shop language, English and Spanish, or mark them for the designer
  (`write-plain-language-copy`).
- MUST NOT name internal functions or tables as requirements. Describe behavior; the tech lead and architect
  choose the design.
- MUST NOT promise dates, prices or plan limits in a spec. Pricing goes through `pricing-experiment` and the
  owner.
- MUST NOT include real buyer or shop data. Use seed names or scrubbed examples (`scrub-pii-fixture`).

## Done when
- `invai-docs/specs/<slug>.md` exists with every template section filled, or marked "n/a" with a reason.
- Each acceptance criterion is Given/When/Then and names a role, a starting state and an observable result.
- Segment effect, success metric with baseline and target, and dependencies are stated.
- Reviews from product-designer, qa-engineer and customer-success are logged in the spec.
- The spec links a scope ref in `product/scope.md`.

## References
- `template.md` (this folder)
- `invai-docs/team/operating-system.md` (wave steps, who reviews whom)
- `invai-docs/research/13-team-gap-analysis.md` §6.2 (task card fields the spec feeds)
- `invai-docs/research/01-shop-workflow.md`, `03-pain-points.md`
- `.claude/agents/product-manager.md` (how the PM decides)
- Related playbooks: `scope-change-request`, `prioritize-backlog`, `acceptance-tests-first`, `define-metric`
