---
name: seed-determinism-review
description: How to prove "seed counts repeat run to run" cheaply (T-P6-4) - content md5 fingerprint, base-vs-head seed, drain-vs-poll pool probe
metadata:
  type: project
---
2026-10-01 T-P6-4: proving seed determinism.
- Fingerprint with content md5s, not only counts: string_agg(order_no:line:unit:state ...) over all items, reprint set by is_reprint (the seed flags original items; `reprint_of_item_id` is null), and a stock_levels row_to_json md5 minus ids/timestamps. Exclude exact `ship_by`/placed timestamps (now-relative) or compare by date.
- Seed the base commit on a third scratch DB at the same hour to judge "golden-path inputs unchanged"; open-order numbers legitimately differ (numbering follows plan order).
- Worktree: `pnpm typecheck` tries to install into a symlinked node_modules and fails; call ./node_modules/.bin/tsc and biome directly.
- B-208 pool probe: start worker on the scratch DB, snapshot pool at exit / after drain / after ~2 min. The pool mover is channels.poll importing mock Shopify #3001/#3002, not the outbox drain.
- Redis slot used by a worker keeps schedulers; flushdb your assigned slot at the end.
