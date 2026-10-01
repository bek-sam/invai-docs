# Review of T-P5-5 (round 1)

- Reviewer: product-designer on Opus 5.5
- Author: web-engineer on Sonnet 5
- Verdict: approve

Scope of this review: `ui` co-review only (copy, states, a11y, i18n fit), per the card. Did not re-run
typecheck/lint/test — that's the primary reviewer's job.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 44c04c1 -- src/i18n/en.ts src/i18n/es.ts` | Read full diff of new `today.alerts.line.*` and `orders.timelineReason.*` keys, en and es |
| Read all 27 screenshots in `/tmp/p5-web/` | Looked at each image; see notes below |
| `stat` on `/tmp/p5-web/*` vs `git log -1 --format=%cI 44c04c1` | Screenshots timestamped 08:29:34–08:37:28; commit at 08:38:06 — shots predate the commit as expected (shoot-then-commit), not stale |
| `grep -n "QC\|control de calidad" src/i18n/es.ts` | Confirmed `qc_fail`/`qc_pass` matches sibling alert-title key `qc_fail_spike` ("control de calidad"); web's QC/"control de calidad" split is a pre-existing inconsistency, not introduced here |
| `grep -n "paquetería\|transportista" src/i18n/es.ts` | New carrier strings ("paquetería") match ~10 existing uses in the same file |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 (Today alert line from kind+params, en/es, date/hour formatting) | Yes | `alerts-panel-en.png` / `-es.png`: "Order #3104011692 ships within 23 hours, due Oct 2, 4:30 AM" / "El pedido #3104011692 se envía en 23 horas, antes del 2 oct, 4:30 a.m." Plural hours (`_other`) and the `order_overdue` line both render correctly in both languages across 11 real alert rows. |
| 2 (timeline reason from reasonCode+reasonParams) | Yes | `order-timeline-en/es-1440.png`: "(Sheet 2026-10-01 #1 received)" / "(Hoja 2026-10-01 #1 recibida)", "(On sheet 2026-10-01 #2)" / "(En la hoja 2026-10-01 #2)" — correct glossary word ("hoja"), no raw keys. |
| 3 (no raw key/internal word/English-in-es, fits at 390/1440) | Yes | No `today.alerts.line.*`/raw key or English leaked into es shots. The commit message itself documents a found-and-fixed bug: a trailing period after Spanish "a.m." (now dropped) — confirmed fixed in `alerts-panel-es.png`. At 390 px, alert detail lines truncate with an ellipsis in **both** en and es (`alerts-panel-en-390.png`, `-es-390.png`) — this is the pre-existing `AlertsPanel` line-clamp, not new; truncation ratio looks the same in both languages so Spanish isn't disproportionately cut. Timeline text wraps cleanly at 390 px with no clipping (`order-timeline-es-390.png`). |
| 4 (unit tests, i18n-es-missing absent for these keys) | Not independently re-run (outside my review scope) | Left to primary reviewer / author's report |

## Blocking findings
None.

## Checks
- [x] Copy matches shop words in `write-plain-language-copy/glossary.md`: hoja, envío/enviar, etiqueta, paquetería all used correctly and consistently with existing strings in the same file.
- [x] No internal words (job, queue, webhook) leaked into copy — `webhook_stuck` deliberately avoids the word "webhook" in both languages.
- [x] Tú-form, natural Mexican/US Spanish throughout; no word-for-word translation artifacts.
- [x] Numbers and dates readable in both languages (Intl-formatted, locale-correct a.m./p.m., no double punctuation).
- [x] Consistent with existing alert headlines/timeline badges (same component, same visual language, status colors unchanged).
- [x] Dark mode checked (`alerts-panel-en-dark.png`, `order-en-dark-1440.png`, `order-es-dark-1440.png`) — contrast and status colors fine.

## Optional notes (not blocking)
- `qc_fail`/`qc_pass` translate as "Falló/Pasó el control de calidad" in the new timeline-reason keys, while other nearby web strings (`qcFails`, `Taller: QC, empaque y etiquetas`) keep "QC" untranslated. This matches the closest sibling (`qc_fail_spike`), so it's not a new bug, but it's the same "pick one and glossary it" gap already called out for "transfer" in `glossary.md`. Worth a glossary decision in a later pass, not this card.
- Not independently verified: unit tests and `scripts/i18n-es-missing.json` status (acceptance criterion 4) — outside the ui-copy/screenshot scope of this co-review.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
