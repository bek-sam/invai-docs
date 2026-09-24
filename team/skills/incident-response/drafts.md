# Incident drafts (for the owner to edit and send)

Agents fill these and queue them with `send-owner-draft`. **Only the owner sends anything outside the team.** Keep facts to what is confirmed; say "we are still checking" for the rest. No buyer PII in any draft: counts and order-number ranges only if the owner asks.

---

## 1. Owner brief (first 30 minutes, inside the team)
```
Incident <YYYY-MM-DD>-<slug>   SEV<1-4>   Status: investigating / contained / resolved
Detected: <time TZ> by <alert / person / shop report>
What's happening, in one line: …
Shops affected: <count, names if known>   Buyer data involved: yes / no / unknown
Contained? <what we did, time>
Clocks: Amazon 24 h notice ends <T0+24h>; shop notices by <T0+24h>; next update <time>
Decisions needed from you: 1) … (OI-<n>)  2) …
IC: <role>. Next update in <30/60> min.
```

## 2. Amazon security notice (owner sends as the Incident Management Point of Contact)
To: security@amazon.com. Send within 24 hours of detection when Amazon information may be involved (research 12 §2.1, §5). Whether a notice is required in a given case is the owner's call.
```
Subject: Security incident notification – InvAI (<Selling Partner API developer/app id, if registered>)

Incident contact: <owner name, email, phone>
Detected: <UTC time>. Current status: <contained / investigating>
What happened: <short factual description>
Data that may be involved: <categories, e.g. buyer name and shipping address>, <approximate count of orders>, <time window>
Amazon data involved: <yes / possibly / no, and why>
Containment done: <tokens revoked, access blocked, secret rotated, at times>
Next steps and next update: <what, by when>
```

## 3. Shop notice (our customers are the controllers of their buyers' data)
Send within 24 hours of detection so each shop can meet its own 72-hour GDPR deadline. English and Spanish (`write-plain-language-copy`); `compliance-officer` reviews the wording.

English:
```
Subject: Security notice about your InvAI account

Hi <shop name>,
On <date> at <time> we found <what happened, in plain words>. It affected <what data, e.g. shipping names and addresses on <n> orders> between <start> and <end>.
What we did: <contained, how>. What you may need to do: <e.g. nothing / tell buyers / re-pair floor tablets>.
We will send the next update by <time>. Questions: reply to this email.
<owner name>, InvAI
```
Spanish:
```
Asunto: Aviso de seguridad sobre tu cuenta de InvAI

Hola <nombre de la tienda>:
El <fecha> a las <hora> detectamos <qué pasó, en palabras sencillas>. Afectó <qué datos, p. ej. nombres y direcciones de envío de <n> pedidos> entre <inicio> y <fin>.
Lo que hicimos: <cómo se contuvo>. Lo que quizás debas hacer: <p. ej. nada / avisar a tus compradores / volver a conectar las tabletas del taller>.
Te enviaremos la próxima actualización antes de <hora>. Si tienes preguntas, responde a este correo.
<nombre del dueño>, InvAI
```

## 4. Shop status update (outage, no data involved)
```
<time TZ> – <what isn't working, in shop words, e.g. "Buying labels is failing">. Orders, gang sheets and the floor still work. We're fixing it and will update by <time>.
<hora> – <qué no funciona, p. ej. "La compra de etiquetas está fallando">. Los pedidos, los gang sheets y el taller siguen funcionando. Lo estamos arreglando y avisaremos antes de <hora>.
```

## 5. Marketplace or partner notices (Shopify, Etsy, TikTok, Walmart, EasyPost)
Per each partner's terms (research 12 §2.2–2.3). Draft the same facts as section 2; the compliance-officer checks which partners must be told and by when.
