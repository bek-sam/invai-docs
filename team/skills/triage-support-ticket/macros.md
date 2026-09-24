# Issue entry format and starter macros

## Entry in `invai-docs/customers/issues.md` (created on first use by `triage-support-ticket`)
```
## ISS-<n>: <symptom in the shop's words>   status: open | workaround | fixed (wave n) | not a bug
- Shops: <slug> (YYYY-MM-DD), <slug> (YYYY-MM-DD)     Severity: S1 | S2 | S3 | S4
- Where: <screen or station>, role <role>, channel <channel>
- Affected: <n orders / items>, oldest ship-by <date time TZ>
- Class: product wrong | needs training | unusual data
- Repro (seed stack): 1. ... 2. ...   Expected: ...  Actual: ...
- Evidence: <scrubbed file or cropped screenshot path>
- Owner role: <role (area)>   Card: <T-n-k or backlog id>
- Workaround: <what the shop does today>
- Reply draft: <owner-inbox id>
```

## Starter macros
Save the ones you use in `invai-docs/customers/macros/<slug>.md` (the folder is created on first use by `triage-support-ticket`). Fill the brackets; keep the tone plain and calm.

### Received, S1 (EN)
"Thanks for telling us. We see that [what's broken] and that [n] orders due [today at time] are affected. For now, please [workaround]. We'll update you by [time]."

### Recibido, S1 (ES)
"Gracias por avisarnos. Vemos que [qué falla] y que hay [n] pedidos que vencen [hoy a la hora]. Por ahora, por favor [solución temporal]. Le avisamos antes de [hora]."

### Wrong print risk, S2 (EN)
"Please hold these orders before pressing: [order numbers]. Put them on hold in Orders so no one presses them. We're checking why [what happened] and will update you by [time]."

### Riesgo de impresión incorrecta, S2 (ES)
"Por favor, no planche estos pedidos todavía: [números]. Póngalos en espera en Pedidos para que nadie los planche. Estamos revisando por qué [qué pasó] y le avisamos antes de [hora]."

### How-to, training (EN)
"You can do this in [screen]: [2–4 numbered steps]. Here's a short guide: [help article]."

### Cómo hacerlo (ES)
"Puede hacerlo en [pantalla]: [2–4 pasos]. Aquí hay una guía corta: [artículo de ayuda]."

### Fixed (EN / ES)
"This is fixed as of [date]. [What changed, one line]. If you still see it, reply and tell us the order number."
"Ya está arreglado desde el [fecha]. [Qué cambió]. Si todavía lo ve, respóndanos con el número de pedido."

Check Spanish screen names against `invai-web/src/i18n/es.ts` and `invai-floor/src/i18n/es.ts` (for example Orders is "Pedidos").
