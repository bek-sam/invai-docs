# Analytics event taxonomy

Owner: data-analyst. An event exists here before anyone instruments it (`instrument-analytics-event`). Status 2026-09-28: **draft, nothing instrumented, no analytics vendor chosen.** A vendor (PostHog is planned in `tools-stack.md`) is a new sub-processor and needs the owner's decision; until then, server events can be counted from InvAI's own tables (e.g. `digest_clicks`), which is how `action_adoption_rate` works today.

Rules for every event: `company_id` (UUID) always; `user_id` or `station_id` for who; ids, enums, counts, cents, durations only. Never buyer data, order numbers shown to buyers, design names, listing text, free text or URLs with query strings. Name `object_action`, past tense, snake_case.

## Analytics v2 events (feed `specs/business-analytics-v2.md` success metrics)
| Event | Fires when | Where | Properties | Feeds |
|---|---|---|---|---|
| `analytics_view_opened` | an analytics screen or tab renders with data | web | `view` (enum: profit, contribution, leakage, shipping, bridge, operations, inventory, lifecycle), `period_days` (int), `role` | weekly active analytics use |
| `analytics_export_downloaded` | a CSV export finishes | server | `view`, `rows` (int) | export use |
| `analytics_action_shown` | an action appears on Today's actions panel | server | `detector` (enum D1–D13), `impact_cents` (int), `rank` (int) | `action_adoption_rate` (Today) |
| `analytics_action_clicked` | the action's button is used | server (click route) | `detector`, `rank` | `action_adoption_rate` (Today) |
| `cost_setting_suggestion_accepted` | the owner saves a setting from a suggestion (labor minutes, lead time) | server | `setting` (enum: labor_minutes, lead_time_days) | measured-cost adoption |
| `assistant_tool_called` | a v6 assistant tool runs | server | `tool` (enum), `rows` (int), `lang` (en, es) | assistant adoption (already derivable from `assistant_messages.toolCalls`) |

## Change log
| Date | Change |
|---|---|
| 2026-09-28 | First draft (analytics v2) |
