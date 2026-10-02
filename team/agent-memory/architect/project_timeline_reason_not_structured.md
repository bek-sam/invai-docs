---
name: project-timeline-reason-not-structured
description: TimelineEntry's from/to are typed but the reason text is not — only folded into the free-text message string
metadata:
  type: project
---

`TimelineEntry.from`/`.to` (`invai-contracts/src/schemas/orders.ts:230-231`) are real typed state-code fields,
safe for a consumer to translate without a contract change. The transition `reason` is not: it's a free-text
column (`orderItemTransitions.reason`) that `orders/service.ts:639` folds into the composed English `message`
string only; `meta` (`t.data`) never receives it (`state-machine.ts:70-78` doesn't copy `opts.reason` into
`opts.data`). Any card that wants to translate a timeline reason (T-P2-4 B-223, B-224's alert bodies have the
same shape) needs an additive `reasonCode`/params field, not message-parsing.

**Why:** caught during P2 plan review — T-P2-4's card claimed "no contract change" based on from/to being
typed, but scoped AC2 (reason translation) in a way only achievable by regexing the backend's untyped display
string from a web-only card with contracts read-only.

**How to apply:** when a future card wants to show a translated reason/detail from an audit or timeline entry,
check whether the value is a typed field or only baked into a free-text message/summary string before approving
the card's "no contract change" premise. See [[project_wave22_25_plan_review_findings]] for the related
"field-name collisions" and "scan never throws" pattern of catching these in plan review.
