---
name: digest-plan-usage-locator
description: How to locate the digest page's "Plan usage" section in e2e tests, and the es-US grouping rule for digest numbers
metadata:
  type: project
---

`/digests/<weekKey>`'s plan-usage block is a `Section` (`invai-web/src/components/page.tsx`) that
renders its title in an `<h2>`, sibling to a content `<div>` inside one `<section>` ancestor. Locate
it with `page.locator("h2", { hasText: /^Plan usage$/ }).locator("xpath=ancestor::section[1]")` (en)
or `/^Uso del plan$/` (es), then assert text within that scoped locator.

**Why:** T-20-2 AC4 was originally written against `settings/billing.tsx`, which the tech lead moved
out of scope (backlog B-184); the real bug (gate issue 5) was the digest page's own plan-usage
numbers. Also: the PM's es-US decision (`specs/weekly-digest.md`, T-20-1 review) means digest
numbers group with a comma in Spanish too ("10,000"), never the bare-`es` locale's period grouping
("10.000") — don't assume Spanish digest text uses period-grouped thousands even though other InvAI
Spanish copy might.

**How to apply:** When writing or updating digest-page acceptance tests, scope assertions to the
named `Section` via its `h2` heading rather than asserting on the whole page, and check digest
numbers against es-US grouping, not bare-`es`. See [[fixture_iso_week_offset]] for other digest
seed-timing traps.
