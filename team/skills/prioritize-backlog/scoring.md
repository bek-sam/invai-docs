# Backlog scoring guide

Score 1–5. Write one line of evidence for each score.

| Factor | 1 | 3 | 5 |
|---|---|---|---|
| **Pain** (which ranked pain from `research/03-pain-points.md`, or which support severity) | Annoyance, pains #9–12 | Costs staff time daily, pains #5–8 | Blocks shipping or causes a wrong print; pains #1–4 |
| **Shops** (who has it, by segment) | One shop | Most pilots, or one whole segment | Every segment, small to large |
| **Confidence** (how sure we are) | Our guess | One pilot's words or research only | Pilot data plus a metric |
| **Effort** (tech lead's estimate) | Hours, one repo | One wave card | Several cards or a contract change across repos |
| **Risk** (IP, security, marketplace policy, money, data) | None | Touches payments, PII or a marketplace rule | Could get a shop suspended or leak buyer data |

`priority = (pain × shops × confidence) / (effort × risk)`

**Approval flag:** `none` | `pending: <program>`. Pending items rank below all usable items.

## Ranking table (copy into `invai-docs/product/backlog-ranking.md`)

```
## YYYY-MM-DD ranking (for wave <n>)

| Rank | Item (id, link) | Source | Pain | Shops | Conf. | Effort | Risk | Approval | Priority | Spec | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|

Always in scope this wave: <bugs, security, incidents, compliance deadlines>
Proposed wave (≤5): 1. ... 2. ...
Not now, out of scope: <item: reason, SCR link if filed>
Not now, waiting on approval: <item: program>
What changed and why: <3–5 lines>
```
