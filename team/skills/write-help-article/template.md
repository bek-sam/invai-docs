---
slug: <kebab-slug>
lang: en            # es for the Spanish file
roles: [office]     # owner | admin | office | designer | presser | packer | receiver | vendor
device: desktop     # desktop | phone | tablet
screens: [Orders]   # names exactly as in nav.ts / i18n
checked_against: <git -C invai-web log -1 --oneline> on YYYY-MM-DD
---

# <Symptom in the reader's words, e.g. "My order says Needs mapping">

**What you see:** <the exact message, badge or screen state, as the app shows it>

**Why:** <one or two lines, in shop words>

## Fix it
1. Go to **<Screen>** (<where it is in the left menu>).
2. <One action per step, with the exact button name.>
3. <...>

![<what the screenshot shows>](../img/<slug>/<file>.png)

## Check it worked
<What the reader should now see, e.g. the order moves to Ready and shows on Today.>

## Still stuck?
- Stop and contact support if <risk condition: e.g. the press screen shows green for the wrong shirt, or orders due today can't get a label>.
- Send: the order number, a screenshot, and the time it happened. Don't send the buyer's address.

Related: <links to other help articles>

<!--
Spanish version: same slug in help/es/, same structure. Section headings:
"Lo que ve", "Por qué", "Cómo arreglarlo", "Cómo comprobar que funcionó", "¿Sigue con el problema?"
Use the app's es labels exactly (invai-web/src/i18n/es.ts, invai-floor/src/i18n/es.ts).
-->
