---
name: fk-coverage-review-pattern
description: T-22-2 — composite-FK coverage tests only see existing FKs; query uuid *_id columns with no FK at all, and mutation-test with a probe table
metadata:
  type: feedback
---

2026-09-29 T-22-2: a pg_constraint-based "every tenant FK is composite" test is blind to reference columns that have NO FK (≈30 in invai, e.g. order_items.design_id, designs.personalization_template_id → S-39). Query pg_attribute for uuid `%_id` columns in company_id tables not in any conkey. Also it doesn't catch swapped column order or nullable company_id (MATCH SIMPLE skips).

**Why:** the card AC said "every FK", so the author and primary review closed S-26 fully; the gap was in columns never constrained.
**How to apply:** for FK/tenancy cards, prove with a probe table (`create table zz_probe(... references orders(id))`) in your own test DB and a psql insert as invai_app with `set local app.company_id`, then drop/rollback. Run tests from `git archive <sha>` to avoid other cards' WIP in the tree.
Related: [[v1-review-staleness-pattern]]
