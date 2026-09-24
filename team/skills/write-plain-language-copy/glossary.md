# InvAI shop words (en → es)

Taken from the shipped catalogs on 2026-09-24 (`invai-web/src/i18n/es.ts`, `invai-floor/src/i18n/es.ts`). Use these words; don't invent synonyms. If a word isn't here, grep both catalogs first: `grep -n '<word>' invai-web/src/i18n/es.ts invai-floor/src/i18n/es.ts`.

| English (UI word) | Spanish | Notes |
|---|---|---|
| order | pedido | "Pedido equivocado" |
| order item | artículo / "unidad" in explanations | one physical shirt; never "line item" in UI |
| blank (the garment) | prenda | "Escanea la prenda" |
| design | diseño | |
| transfer (printed DTF film piece) | transferencia (floor) / transfer (web) | **Inconsistent today.** Floor says "Transferencia", web says "Transfer". Match the app you are editing and flag it to the product-designer |
| gang sheet | gang sheet | kept in English in both languages ("Armar gang sheets") |
| sheet | hoja | "Hojas", "Hoja cancelada" |
| film | film | "Film + tinta por pulgada cuadrada" |
| press (verb) / presser | planchar / planchador | station "Plancha 1" |
| floor (production area) | taller | app title "InvAI Taller" |
| station | estación | "Estación conectada" |
| QC | control de calidad (floor), QC (web) | |
| pack / packer | empacar / empacador | |
| bin / tote | caja | "Escanea una caja para el pedido {{orderNo}}" |
| label (shipping) | etiqueta | "por etiqueta", "Etiquetas" |
| ship by | enviar antes de | |
| at risk | en riesgo | |
| on hold | en espera | |
| reprint | reimpresión | |
| receive | recibir | "Recibir ahora" |
| vendor (DTF print vendor) | proveedor | |
| profit | ganancia(s) | |
| shipping | envío(s) | |
| SKU | SKU | "Códigos SKU" |

## Roles as users see them
owner, admin, office, designer, presser, packer, receiver, vendor (`invai-contracts/src/roles.ts`). In copy say what the person does ("the person at the press"), not the permission name.

## Words to avoid in UI copy
- Internal names: tenant, company_id, RLS, job, queue, outbox, webhook, payload, procedure, mock, SKU rule regex.
- Vague errors: "Something went wrong", "Invalid input", "Error 500".
- Blame: "You entered the wrong …". Say what happened and what to do.
