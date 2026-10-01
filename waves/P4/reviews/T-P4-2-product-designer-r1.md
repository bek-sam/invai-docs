# Review of T-P4-2 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: floor-engineer on Sonnet 5
- Verdict: approve

Scope: co-review for copy, glossary, layout and Spanish quality (risk flag `ui`). Reviewed the final
state after both commits (`0b98f85`, round 1 copy; `b2cfd13`, round 2 fix for `reviewer`'s r1 finding).

## Evidence I looked at
- Card `T-P4-2-floor-es-pass.md`, report `reports/T-P4-2.md`, `reviewer` r1 (changes-required) and r2
  (approve) verdicts.
- Diffs `git -C invai-floor show 0b98f85 b2cfd13`.
- Screenshots at 1280×800 in `/tmp/p4-floor/`: `01`/`02` (pre-fix, round 1 copy), `r2-01`/`r2-02`
  (post-fix, round 2 copy), `04`-`05` (QC pass/fail, en+es), `06`-`07` (busy panel OK and
  wrong-blank-blocked, es).
- Glossary (`.claude/skills/write-plain-language-copy/glossary.md`).
- `invai-ui/src/floor/station-header.tsx` source, to judge the reported wrap finding.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `r2-02-header-pending12-review2-es.png`: "12 escaneos sin enviar" + "2 por revisar" both one line, visible free space to the right. `r2-01-header-pending1-es.png`: singular "1 escaneo sin enviar" correct (`_one` form). Meaning now matches English ("N scans waiting to sync") — "sin enviar" reuses this catalog's own `outbox.title: "Sin enviar"` rather than the shipping sense of "enviar antes de" (glossary: ship by). Good fix over round 1's "por enviar", which I would also have blocked. |
| 2 | Yes | `04-qc-pass-es.png` "APROBADO" / "Aprobado: pedido 113-2324316-1004628"; `05-qc-fail-es.png` "RECHAZADO" / "Reimpresión pedida: pedido 3104011729" — past-tense result text distinct from the button ("Aprobar"/"Rechazar" not shown here, this is the result screen), order number visible, no wrap/clip. "Reimpresión" matches glossary. EN (`04-qc-pass-en.png`) confirms floor's own convention is a bare order number, no "#" (unlike web's `orderLabel()`) — consistent in both languages, not a bug. |
| 3 | Yes | `06-busy-ok-es.png`: correct blank, green PRENSAR panel, amber "Ocupado — confirmando en 25 s" sub-line, no clip, no raw key. `07-busy-wrong-blocked-es.png`: wrong color, stays red BLOQUEADO with "Necesita: … / Escaneado: …" and the same busy sub-line — busy state never overrides the block, which is the important invariant here. |
| 4 | Not my check | `reviewer` confirmed 112/112 unmodified; I didn't re-run. |

## Station-header crowding claim (report's "Known gaps")
The report flags `invai-ui/src/floor/station-header.tsx` as wrapping the operator name ("Pat
Presser") and the "En línea" badge at 1280×800 under the same crowded-header condition as B-241.
I read the component (flex row, `justify-between`, no `truncate`/`shrink-0` on the name or status
spans — so it theoretically *could* wrap under a long enough name or enough right-side content) and
checked every floor screenshot provided, including the busiest ones: the pre-fix 12-pending +
2-review case (`02-header-pending12-review2-es.png`, the longest copy tested) and both post-fix
cases. In all of them "Pat Presser" and "En línea" stay on one line with visible slack before the
EN/ES toggle. I can't confirm the wrap from this evidence.
This isn't a false alarm to dismiss outright — the component genuinely has no overflow guard, and a
longer operator name (common with two surnames, e.g. "María Hernández-Domínguez") could still break
it — but as tested here it doesn't reproduce. Recommend: file a low-severity backlog row for
`station-header.tsx` to add `truncate`/`min-w-0` defensively, but not block this card on it, and ask
whoever opens that row to attach a screenshot that actually reproduces the wrap (e.g. a long name at
1280×800) rather than describe it from the code alone.

## Optional notes (not blocking)
- QC footer plural: `04-qc-pass-es.png` shows "2 pendientes · 17 hechos hoy"; `05-qc-fail-es.png`
  shows "1 pendientes · 18 hechos hoy" — should be singular "1 pendiente". Pre-existing, not part of
  this diff, not in this card's owned paths. Worth a one-line follow-up card.
- `outbox.parked_one/_other` kept as "por revisar" (round 2, left unchanged per reviewer's optional
  note): fine. Generic "review" word, distinct from "control de calidad" (QC), fits in `r2-02`.

## Checks
- [x] Only owned paths changed (per `reviewer`'s re-run of `git diff --stat`, not re-verified by me)
- [x] Nothing outside scope
- [x] n/a — no tests in my remit; `reviewer` confirmed none weakened
- [x] en/es: both present, glossary words used correctly after the round-2 fix; placeholders kept
- [x] Decisions: none needed
