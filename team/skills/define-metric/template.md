# Metric: <snake_case_name>

- **Label:** EN "<Late orders>" / ES "<Pedidos tarde>"
- **Version:** 1 (YYYY-MM-DD)   **Owner (acts on it):** <role>   **Defined by:** data-analyst

## Meaning
<One sentence a shop owner would agree with.>

## Formula
- Numerator:
- Denominator:
- Window and time zone:
- Excludes:
- Unit: <pct as 6.5 | ratio 0..1 | cents | minutes>
- Minimum sample: <n events>; below it, report counts only

## Source
| Table.column | Meaning |
|---|---|

Enums used: <e.g. ORDER_ITEM_STATES, REPRINT_REASONS>

## Marketplace comparison (if any)
<The marketplace's own rule, with a link, and how InvAI's number differs.>

## SQL
Path: `invai-backend/scripts/analytics/<name>.sql`
Tested: YYYY-MM-DD on <database>, result <summary>; spot-checked <n> rows by hand.

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large) | | |
| Channel | | |
| Station / role | | |

## Target and alarm
- Target:
- Alarm (goes into the weekly review):

## Caveats
- Seed vs real data, estimates, mocks, what it can't see.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
